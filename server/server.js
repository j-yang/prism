require('dotenv').config();
const express = require('express');
const multer = require('multer');
const SftpClient = require('ssh2-sftp-client');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { EventEmitter } = require('events');

// 增加最大监听器数量以防止内存泄漏警告
EventEmitter.defaultMaxListeners = 20;

// 设置进程级别的优化
process.env.UV_THREADPOOL_SIZE = 128; // 增加线程池大小
process.setMaxListeners(20);

const app = express();
const PORT = process.env.PORT || 3001;
// 在文件顶部的其他 require 语句之后添加
const upload = multer({
  dest: 'uploads/', // 临时文件存储目录
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB 文件大小限制
  },
  fileFilter: (req, file, cb) => {
    // 允许的文件类型
    const allowedTypes = [
      'text/plain',
      'application/x-sas',
      'application/octet-stream'
    ];

    const allowedExtensions = ['.sas', '.txt', '.log', '.lst'];
    const fileExtension = path.extname(file.originalname).toLowerCase();

    if (allowedTypes.includes(file.mimetype) || allowedExtensions.includes(fileExtension)) {
      cb(null, true);
    } else {
      cb(new Error('不支持的文件类型'), false);
    }
  }
});

// 确保 uploads 目录存在
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
  console.log('已创建 uploads 目录');
}

// 中间件配置 - 添加更多优化
app.use(cors({
  origin: true,
  credentials: true,
  optionsSuccessStatus: 200
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 设置服务器超时
app.use((req, res, next) => {
  req.setTimeout(120000); // 2分钟超时
  res.setTimeout(120000);
  next();
});

// 存储活动的SFTP连接
const connections = new Map();
let currentConnectionId = null;

// 连接池管理
class ConnectionPool {
  constructor() {
    this.pool = new Map();
    this.maxConnections = 5; // 限制最大连接数
    this.connectionTimeout = 30 * 60 * 1000; // 30分钟超时
  }

  async getConnection(connectionId, config) {
    // 检查是否已有连接
    if (this.pool.has(connectionId)) {
      const pooled = this.pool.get(connectionId);
      if (Date.now() - pooled.lastUsed < this.connectionTimeout) {
        pooled.lastUsed = Date.now();
        return pooled.sftp;
      } else {
        // 连接已过期，清理它
        await this.removeConnection(connectionId);
      }
    }

    // 如果连接池已满，清理最老的连接
    if (this.pool.size >= this.maxConnections) {
      await this.cleanupOldConnections();
    }

    // 创建新连接
    const sftp = new SftpClient();
    await sftp.connect(config);

    this.pool.set(connectionId, {
      sftp,
      lastUsed: Date.now(),
      config
    });

    return sftp;
  }

  async removeConnection(connectionId) {
    if (this.pool.has(connectionId)) {
      const pooled = this.pool.get(connectionId);
      try {
        await pooled.sftp.end();
      } catch (error) {
        console.error(`清理连接失败: ${connectionId}`, error.message);
      }
      this.pool.delete(connectionId);
    }
  }

  async cleanupOldConnections() {
    const now = Date.now();
    const toRemove = [];

    for (const [connectionId, pooled] of this.pool.entries()) {
      if (now - pooled.lastUsed > this.connectionTimeout) {
        toRemove.push(connectionId);
      }
    }

    // 如果没有过期的连接，移除最老的
    if (toRemove.length === 0 && this.pool.size > 0) {
      const oldest = Array.from(this.pool.entries())
        .sort((a, b) => a[1].lastUsed - b[1].lastUsed)[0];
      toRemove.push(oldest[0]);
    }

    for (const connectionId of toRemove) {
      await this.removeConnection(connectionId);
    }
  }

  async cleanup() {
    const connectionIds = Array.from(this.pool.keys());
    for (const connectionId of connectionIds) {
      await this.removeConnection(connectionId);
    }
  }
}

// 在 ConnectionPool 类定义之后添加
async function cleanupConnection(connectionId) {
  try {
    if (connections.has(connectionId)) {
      const connection = connections.get(connectionId);
      await connection.sftp.end();
      connections.delete(connectionId);
      console.log(`已清理连接: ${connectionId}`);
    }

    // 同时从连接池中移除
    await connectionPool.removeConnection(connectionId);
  } catch (error) {
    console.error(`清理连接失败: ${connectionId}`, error.message);
  }
}
const connectionPool = new ConnectionPool();

// 连接到SFTP服务器
app.post('/api/server/connect', async (req, res) => {
  try {
    console.log('收到连接请求');
    const { host, port, username, password, protocol } = req.body;

    // 验证必要参��
    if (!host || !username || !password) {
      console.log('缺少必要的连接参数');
      return res.status(400).json({ error: '缺少必要的连接参数' });
    }

    if (protocol !== 'sftp') {
      console.log('不支持的协议:', protocol);
      return res.status(400).json({ error: '目前只支持SFTP协议' });
    }

    // 生成连接ID
    const connectionId = `${username}@${host}:${port}`;

    // 清理现有连接以防止连接泄露
    if (currentConnectionId && connections.has(currentConnectionId)) {
      console.log('清理现有连接...');
      await cleanupConnection(currentConnectionId);
    }

    // 连接配置 - 增加超时和重试设置
    const config = {
      host: host,
      port: port || 22,
      username: username,
      password: password,
      readyTimeout: 30000, // 增加超时时间
      retries: 3, // 增加重试次数
      retry_factor: 2,
      retry_minTimeout: 2000,
      keepaliveInterval: 10000, // 保持连接活跃
      keepaliveCountMax: 3,
      hostVerifier: false, // 跳过主机验证（仅用于调试）
      readyTimeout: 60000, // 增加超时时间
      algorithms: {
        kex: [
          'diffie-hellman-group14-sha256',
          'diffie-hellman-group16-sha512',
          'diffie-hellman-group14-sha1',
          'diffie-hellman-group1-sha1'
        ],
        cipher: [
          'aes128-ctr',
          'aes192-ctr',
          'aes256-ctr',
          'aes128-cbc',
          'aes256-cbc'
        ],
        serverHostKey: [
          'ssh-rsa',
          'ssh-dss'
        ],
        hmac: [
          'hmac-sha2-256',
          'hmac-sha1'
        ]
      },
      // 添加调试选项
      debug: process.env.NODE_ENV === 'development' ? (msg) => console.log('SFTP Debug:', msg) : undefined
    };

    console.log(`尝试连接到: ${username}@${host}:${port}`);

    try {
      // 使用连接池获取连接
      const sftp = await connectionPool.getConnection(connectionId, config);
      console.log('SFTP连接成功');

      // 测试连接是否真的可用
      try {
        await sftp.list('/');
        console.log('连接测试成功');
      } catch (listError) {
        console.log('连接测试失败，尝试使用默认路径');
        // 如果根目录不可访问，这不是致命错误
      }

    } catch (connectError) {
      console.error('SFTP连接失败:', connectError);

      // 提供更详细的错误信息
      let errorMessage = 'SFTP连接失败';
      let userFriendlyMessage = '连接失败';

      if (connectError.code === 'ENOBUFS') {
        errorMessage = '网络缓冲区不足，请稍后重试';
        userFriendlyMessage = '网络连接繁忙，请稍后重试';

        // 对于ENOBUFS错误，清理连接池并强制垃圾回收
        console.log('检测到ENOBUFS错误，清理连接池...');
        await connectionPool.cleanup();
        if (global.gc) {
          global.gc();
        }
      } else if (connectError.code === 'ECONNREFUSED') {
        errorMessage = '连接被拒绝，请检查主机和端口';
        userFriendlyMessage = '无法连接到服务器，请检查连接信息';
      } else if (connectError.code === 'ENOTFOUND') {
        errorMessage = '主机名未找到';
        userFriendlyMessage = '无法找到服务器，请检查主机名';
      } else if (connectError.code === 'ETIMEDOUT' || connectError.message.includes('timeout')) {
        errorMessage = '连接超时';
        userFriendlyMessage = '连接超时，请检查网络连接';
      } else if (connectError.level === 'client-authentication') {
        errorMessage = '身份验证失败';
        userFriendlyMessage = '用户名或密码错误';
      }

      return res.status(500).json({
        error: userFriendlyMessage,
        message: errorMessage,
        details: {
          code: connectError.code,
          level: connectError.level,
          host: host,
          port: port || 22
        }
      });
    }

    // 获取连接池中的连接信息
    const pooledConnection = connectionPool.pool.get(connectionId);

    // 存储连接引用
    connections.set(connectionId, {
      sftp: pooledConnection.sftp,
      config: config,
      lastUsed: Date.now()
    });

    currentConnectionId = connectionId;
    console.log('连接成功，connectionId:', connectionId);

    res.json({
      success: true,
      connectionId: connectionId,
      initialPath: '/SASDATA2/SafetyNet/'
    });

  } catch (error) {
    console.error('连接处理失败:', error);
    console.error('错误堆栈:', error.stack);

    res.status(500).json({
      error: '连接失败',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
});

// 断开连接
app.post('/api/server/disconnect', async (req, res) => {
  try {
    const connectionId = currentConnectionId;

    if (connectionId && connections.has(connectionId)) {
      await cleanupConnection(connectionId);
    }

    currentConnectionId = null;
    res.json({ success: true });
  } catch (error) {
    console.error('断开连接失败:', error.message);
    res.status(500).json({ error: '断开连接失败' });
  }
});

// 获取文件列表
app.get('/api/server/files', async (req, res) => {
  try {
    const connectionId = currentConnectionId;
    const targetPath = req.query.path || '/SASDATA2/SafetyNet/';

    console.log(`获取文件列表: ${targetPath}`);

    if (!connectionId || !connections.has(connectionId)) {
      return res.status(401).json({ error: '未连接到服务器' });
    }

    const connection = connections.get(connectionId);
    const sftp = connection.sftp;

    // 更新最后使用时间
    connection.lastUsed = Date.now();

    const files = await sftp.list(targetPath);
    console.log(`找到 ${files.length} 个文件/文件夹`);

    const fileList = files.map(file => ({
      name: file.name,
      type: file.type === 'd' ? 'directory' : 'file',
      size: file.size,
      lastModified: new Date(file.modifyTime),
      path: path.posix.join(targetPath, file.name)
    }));

    res.json(fileList);

  } catch (error) {
    console.error('获取文件列表失败:', error.message);
    res.status(500).json({
      error: '获取文件列表失败',
      message: error.message
    });
  }
});

// 上传文件
app.post('/api/server/upload', upload.single('file'), async (req, res) => {
  try {
    const connectionId = currentConnectionId;
    const remotePath = req.body.path;
    const localFile = req.file;

    if (!connectionId || !connections.has(connectionId)) {
      return res.status(401).json({ error: '未连接到服务器' });
    }

    if (!localFile) {
      return res.status(400).json({ error: '没有上传文件' });
    }

    const connection = connections.get(connectionId);
    const sftp = connection.sftp;

    // 更新最后使用时间
    connection.lastUsed = Date.now();

    console.log(`上传文件: ${localFile.originalname} 到 ${remotePath}`);

    // 上传文件到服务器
    await sftp.put(localFile.path, remotePath);

    // 删除临时文件
    fs.unlink(localFile.path, (err) => {
      if (err) console.error('删除临时文件失败:', err);
    });

    console.log(`文件上传成功: ${localFile.originalname}`);

    res.json({
      success: true,
      message: '文件上传成功',
      remotePath: remotePath,
      fileName: localFile.originalname
    });

  } catch (error) {
    console.error('文件上传失败:', error.message);

    // 删除临时文件
    if (req.file) {
      fs.unlink(req.file.path, (err) => {
        if (err) console.error('删除临时文件失败:', err);
      });
    }

    res.status(500).json({
      error: '文件上传失败',
      message: error.message
    });
  }
});

// 健康检查
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    activeConnections: connections.size,
    version: '1.0.0'
  });
});

// 清理过期连接（每10分钟检查一次）
setInterval(() => {
  const now = Date.now();
  const timeout = 30 * 60 * 1000; // 30分钟超时

  for (const [connectionId, connection] of connections.entries()) {
    if (now - connection.lastUsed > timeout) {
      console.log(`清理过期连接: ${connectionId}`);
      connection.sftp.end().catch(err => console.error('关闭连接失败:', err));
      connections.delete(connectionId);
    }
  }
}, 10 * 60 * 1000);

// 全局错误处理
app.use((error, req, res, next) => {
  console.error('服务器错误:', error.message);
  res.status(500).json({
    error: '服务器内部错误',
    message: error.message
  });
});

// 404处理 - 只处理API路径
app.use('/api/*', (req, res) => {
  res.status(404).json({
    error: '接口不存在',
    path: req.path
  });
});

// 对于非API路径，返回简单���状态信息
app.use((req, res) => {
  if (req.path.startsWith('/api/')) {
    res.status(404).json({
      error: '接口不存在',
      path: req.path
    });
  } else {
    res.status(404).json({
      error: '此服务器仅处理API请求',
      message: '请访问前端应用端口 3000'
    });
  }
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`PRISM服务器已��动`);
  console.log(`端口: ${PORT}`);
  console.log(`健康检查: http://localhost:${PORT}/api/health`);
  console.log(`时间: ${new Date().toLocaleString()}`);
});

// 优雅关闭
process.on('SIGINT', async () => {
  console.log('\n正在关闭服务器...');

  // 关闭所有SFTP连接
  for (const [connectionId, connection] of connections.entries()) {
    try {
      await connection.sftp.end();
      console.log(`已关闭连接: ${connectionId}`);
    } catch (error) {
      console.error(`关闭连接失败: ${connectionId}`, error.message);
    }
  }

  console.log('服务器已关闭');
  process.exit(0);
});
