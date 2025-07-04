# GitHub Pages 404 错误排查指南

## 立即检查步骤

### 1. 确认GitHub Actions状态
访问: `https://github.com/[你的用户名]/[仓库名]/actions`
- 查看最近的工作流是否成功（绿色✅）
- 如果失败（红色❌），点击查看错误日志

### 2. 检查Pages设置
访问: `https://github.com/[你的用户名]/[仓库名]/settings/pages`
- Source 应该设置为 "GitHub Actions"
- 如果显示 "Deploy from a branch"，改为 "GitHub Actions"

### 3. 确认仓库名称
你的仓库名是什么？访问地址应该是：
```
https://[你的用户名].github.io/[仓库名]/
```

## 常见问题和解决方案

### 问题1：Actions构建失败
**症状**: Actions标签页显示红色❌
**解决**: 
1. 点击失败的workflow查看错误
2. 常见错误：依赖安装失败、TypeScript错误
3. 修复后重新推送代码

### 问题2：路径不匹配
**症状**: 页面加载但资源404
**解决**: 
- 确保vite.config.ts中的base路径与仓库名一致
- 我已经修改为自动检测，应该能解决这个问题

### 问题3：仓库权限问题
**症状**: Actions无法部署
**解决**:
1. 仓库Settings → Actions → General
2. Workflow permissions 选择 "Read and write permissions"
3. 勾选 "Allow GitHub Actions to create and approve pull requests"

### 问题4：首次部署延迟
**症状**: 设置正确但仍然404
**解决**: 
- 首次部署可能需要5-10分钟生效
- 可以尝试强制刷新浏览器（Ctrl+F5）

## 手动部署备用方案

如果自动部署有问题，可以先尝试手动部署：

1. 确保本地环境正常：
   ```bash
   npm install
   npm run build
   ```

2. 使用gh-pages手动部署：
   ```bash
   npm run deploy
   ```

3. 检查gh-pages分支是否创建成功

## 调试命令

本地测试构建：
```bash
npm run build
npm run preview
```

如果本地preview正常，说明代码没问题，是部署配置问题。

## 联系支持

如果以上步骤都尝试了仍然不行，请提供：
1. 你的GitHub仓库链接
2. Actions页面的错误截图
3. 具体的错误信息
