# PRISM 生产环境部署指南

## 概述
本文档描述了如何将 PRISM 应用部署到生产环境，包括前端应用和后端 SFTP 服务器。

## 功能说明
生产环境仅包含以下功能：
- ✅ SFTP 服务器连接
- ✅ 文件夹浏览和导航
- ✅ 文件上传功能
- ✅ 上传进度显示
- ❌ 文件删除功能（已移除）
- ❌ 创建文件夹功能（已移除）

## 环境要求
- Node.js 16+ 
- NPM 或 Yarn
- 服务器访问权限

## 部署步骤

### 1. 后端服务器部署

#### 1.1 进入服务器目录
```bash
cd server
```

#### 1.2 安装依赖
```bash
npm install
```

#### 1.3 配置环境变量
编辑 `.env` 文件：
```
PORT=3001
MAX_FILE_SIZE=50MB
UPLOAD_DIR=uploads
CONNECTION_TIMEOUT=30
READY_TIMEOUT=20000
DEBUG=false
```

#### 1.4 启动服务器
```bash
# 开发环境
npm run dev

# 生产环境
npm start
```

### 2. 前端应用部署

#### 2.1 构建生产版本
```bash
npm run build
```

#### 2.2 部署到服务器
将 `dist` 目录内容部署到 Web 服务器

#### 2.3 配置代理
如果前端和后端在不同端口，需要配置代理：

**Nginx 配置示例：**
```nginx
location /api/ {
    proxy_pass http://localhost:3001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## API 端点

### 连接服务器
```
POST /api/server/connect
Content-Type: application/json

{
  "host": "sesklsasgrnprd04.emea.astrazeneca.net",
  "port": 22,
  "username": "ktxv525",
  "password": "your_password",
  "protocol": "sftp"
}
```

### 获取文件列表
```
GET /api/server/files?path=/home/sasuser/programs
```

### 上传文件
```
POST /api/server/upload
Content-Type: multipart/form-data

file: [文件内容]
path: /home/sasuser/programs/filename.sas
```

### 断开连接
```
POST /api/server/disconnect
```

## 安全考虑

1. **HTTPS**: 生产环境必须使用 HTTPS 协议
2. **密码安全**: 不要在前端代码中硬编码密码
3. **文件大小限制**: 默认限制为 50MB
4. **连接超时**: 30 分钟无活动后自动断开
5. **错误处理**: 敏感信息不会暴露给客户端

## 故障排除

### 常见错误

1. **连接失败**
   - 检查服务器地址和端口
   - 验证用户名和密码
   - 确认网络连接

2. **上传失败**
   - 检查文件大小限制
   - 验证目标路径权限
   - 查看服务器日志

3. **文件列表为空**
   - 检查路径是否存在
   - 验证用户权限
   - 确认 SFTP 连接状态

### 日志查看
```bash
# 查看服务器日志
tail -f server.log

# 查看上传日志
ls -la uploads/
```

## 维护

### 定期任务
- 清理临时上传文件
- 监控服务器性能
- 检查连接状态

### 更新部署
```bash
# 更新后端
cd server
npm install
npm start

# 更新前端
npm run build
# 部署 dist 目录
```

## 联系信息
如有问题，请联系系统管理员。
