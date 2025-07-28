# GitHub Pages 部署问题解决方案

## 问题分析

你遇到的错误主要有两个：

1. **404 Not Found**: `index-C_AZQIv5.js:1 Failed to load resource`
2. **MIME Type 错误**: `Refused to apply style from '...' because its MIME type ('text/html') is not a supported stylesheet MIME type`

这些问题的根本原因是：
- 资源文件路径配置不正确
- GitHub Pages 对 SPA 应用的路由处理需要特殊配置
- 缺少正确的环境变量设置

## 解决方案

我已经为你的项目做了以下修改：

### 1. 创建了 GitHub Actions 工作流 (`.github/workflows/deploy.yml`)
- 自动化部署流程
- 正确设置环境变量
- 使用官方 GitHub Pages Actions

### 2. 更新了 `vite.config.ts`
- 根据环境自动设置 `base` 路径
- 在 GitHub Actions 中使用 `/prism/`，本地开发使用 `/`
- 优化了资源文件的组织结构

### 3. 添加了必要的配置文件
- `.nojekyll` - 告诉 GitHub Pages 不要使用 Jekyll 处理
- `404.html` - 处理 SPA 路由，将所有未找到的页面重定向到主页

### 4. 更新了部署脚本
- 添加了 `deploy:manual` 脚本，正确设置环境变量
- 安装了 `cross-env` 包支持跨平台环境变量

## 部署步骤

### 方法一：使用 GitHub Actions（推荐）
1. 将所有更改推送到 GitHub 仓库
2. 在 GitHub 仓库设置中启用 GitHub Pages
3. 选择 "GitHub Actions" 作为源
4. 每次推送到 main/master 分支时会自动部署

### 方法二：手动部署
运行以下命令：
```bash
npm run deploy:manual
```

## 验证部署

部署完成后，访问：
`https://super-adventure-4j126nm.pages.github.io/prism/`

如果仍有问题，检查：
1. GitHub 仓库设置中的 Pages 配置
2. 构建日志中是否有错误
3. 浏览器开发者工具中的网络请求

## 常见问题

### Q: 页面显示空白
A: 检查浏览器控制台，通常是资源加载失败导致

### Q: CSS 样式不生效
A: 确保 base 路径设置正确，清除浏览器缓存

### Q: 路由不工作
A: 确保 404.html 文件正确配置了 SPA 重定向逻辑
