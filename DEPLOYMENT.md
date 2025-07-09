# PRISM 部署指南

本文档描述如何在不同环境中部署PRISM应用程序。

## 📋 部署前准备

### 系统要求
- **Node.js** >= 18.0.0
- **npm** >= 8.0.0 或 **yarn** >= 1.22.0
- **现代浏览器支持** (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- **内存** >= 4GB RAM (推荐用于大Excel文件处理)
- **存储空间** >= 1GB 可用空间

### 环境检查
```bash
# 检查Node.js版本
node --version

# 检查npm版本
npm --version

# 检查可用内存
# Windows
systeminfo | findstr "Available Physical Memory"
# Linux/Mac
free -h
```

## 🚀 生产环境部署

### 方案一：静态文件部署 (推荐)

#### 1. 构建生产版本
```bash
# 克隆项目
git clone https://github.com/your-repo/prism.git
cd prism

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建结果在 dist/ 目录
```

#### 2. Web服务器配置

**Apache配置 (.htaccess)**
```apache
RewriteEngine On
RewriteRule ^(?!.*\.).*$ /index.html [L]

# 启用压缩
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# 设置缓存
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
    ExpiresByType image/png "access plus 1 month"
    ExpiresByType image/svg+xml "access plus 1 month"
</IfModule>
```

**Nginx配置**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/prism/dist;
    index index.html;

    # 启用压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # 处理单页应用路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1M;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

#### 3. 部署步骤
```bash
# 将dist目录内容上传到web服务器
# 方法1: 使用rsync
rsync -avz dist/ user@server:/path/to/web/root/

# 方法2: 使用FTP/SFTP客户端上传dist目录内容

# 方法3: 使用GitHub Pages (如果使用GitHub)
npm run deploy
```

### 方案二：Docker部署

#### 1. 创建Dockerfile
```dockerfile
# 多阶段构建
FROM node:18-alpine AS builder

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
```

#### 2. Docker部署命令
```bash
# 构建镜像
docker build -t prism:2.0.0 .

# 运行容器
docker run -d -p 80:80 --name prism-app prism:2.0.0

# 或使用docker-compose
version: '3.8'
services:
  prism:
    build: .
    ports:
      - "80:80"
    restart: unless-stopped
```

## 🛠️ 开发环境部署

### 本地开发环境
```bash
# 克隆项目
git clone https://github.com/your-repo/prism.git
cd prism

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

### 开发环境配置
```bash
# 启用类型检查
npm run type-check

# 预览构建结果
npm run build
npm run preview
```

## 🔧 环境变量配置

创建 `.env` 文件（如需要） :
```env
# 基础路径 (如果部署在子目录)
VITE_BASE_URL=/prism/

# API端点 (如果有后端API)
VITE_API_BASE_URL=https://api.your-domain.com

# 应用标题
VITE_APP_TITLE=PRISM

# 启用调试模式
VITE_DEBUG=false
```

## 📊 性能优化

### 构建优化
```javascript
// vite.config.ts
export default defineConfig({
  build: {
    // 代码分割
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'pinia'],
          utils: ['xlsx', 'jszip', 'file-saver']
        }
      }
    },
    // 压缩选项
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
})
```

### CDN加速
```html
<!-- 在index.html中使用CDN -->
<link rel="preload" href="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js" as="script">
```

## 🔒 安全配置

### HTTPS配置
```bash
# 使用Let's Encrypt获取SSL证书
certbot --nginx -d your-domain.com
```

### 安全头配置
```nginx
# 在nginx��置中添加
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

## 📈 监控和日志

### 访问日志
```nginx
# nginx访问日志配置
access_log /var/log/nginx/prism_access.log combined;
error_log /var/log/nginx/prism_error.log;
```

### 应用监控
```javascript
// 添加错误监控
window.addEventListener('error', (event) => {
  console.error('Application Error:', event.error);
  // 发送错误报告到监控服务
});
```

## 🔄 备份和恢复

### 模板数据备份
```bash
# 备份用户模板数据
# 模板存储在浏览器localStorage中
# 建议用户定期导出模板进行备份
```

### 应用代码备份
```bash
# 代码版本控制
git tag v2.0.0
git push origin v2.0.0

# 构建产物备份
tar -czf prism-v2.0.0-dist.tar.gz dist/
```

## 🚨 故障排除

### 常见部署问题

#### 1. 路由404错误
**问题**: 刷新页面或直接访问路由时出现404
**解决**: 配置web服务器支持SPA路由 (参见上面的nginx/apache配置)

#### 2. 静态资源加载失败
**问题**: CSS/JS文件404错误
**解决**: 检查BASE_URL配置和文件路径

#### 3. 内存不足错误
**问题**: 处理大Excel文件时浏览器崩溃
**解决**: 增加服务器内存或优化文件处理逻辑

### 性能问题诊断
```bash
# 检查构建包大小
npm run build
du -sh dist/

# 分析包内容
npx vite-bundle-analyzer dist/
```

## 📞 获取支持

- **部署问题**: [GitHub Issues](https://github.com/your-repo/prism/issues)
- **文档**: [README.md](README.md)
- **社区**: [GitHub Discussions](https://github.com/your-repo/prism/discussions)
