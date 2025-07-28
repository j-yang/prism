# GitHub Pages 部署故障排除指南

## 问题诊断

你遇到的错误：
```
Branch "master" is not allowed to deploy to github-pages due to environment protection rules.
The deployment was rejected or didn't satisfy other protection rules.
```

这表示 GitHub 仓库设置了环境保护规则，阻止了部署。

## 解决方案

### 方案1：检查 GitHub 仓库设置（推荐）

1. 进入你的 GitHub 仓库页面
2. 点击 `Settings` 选项卡
3. 在左侧菜单中找到 `Pages`
4. 检查 "Source" 设置：
   - 应该选择 "GitHub Actions"
   - 不要选择 "Deploy from a branch"

### 方案2：检查环境保护规则

1. 在仓库设置中，点击左侧的 `Environments`
2. 如果存在 `github-pages` 环境，点击它
3. 检查 "Deployment branches" 设置：
   - 选择 "All branches" 或
   - 添加 `master` 分支到允许列表

### 方案3：使用经典的 gh-pages 部署（备用方案）

如果 GitHub Actions 继续有问题，可以回到传统的 gh-pages 部署方式：

```bash
npm run deploy
```

### 方案4：手动触发部署

1. 进入 GitHub 仓库的 `Actions` 选项卡
2. 点击 "Deploy to GitHub Pages" 工作流
3. 点击 "Run workflow" 按钮
4. 选择 `master` 分支并运行

## 验证步骤

部署成功后，检查以下内容：

1. **Actions 选项卡**：确认工作流运行成功（绿色对勾）
2. **Pages 设置**：确认显示部署URL
3. **浏览器测试**：访问部署的URL，检查是否还有资源加载错误

## 如果仍有问题

1. **清除浏览器缓存**：强制刷新页面（Ctrl+F5）
2. **检查构建日志**：在 Actions 中查看详细的构建和部署日志
3. **验证文件结构**：确认 `dist` 目录中包含正确的文件

## 联系信息

如果上述方案都无效，请提供：
- GitHub Actions 的完整错误日志
- 仓库的 Pages 设置截图
- 环境保护规则的详细信息
