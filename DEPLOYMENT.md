# PRISM 平台 GitHub Pages 部署指南

## 部署方式

### 方式一：自动部署（推荐）
当你推送代码到 `main` 分支时，GitHub Actions 会自动构建并部署到 GitHub Pages。

### 方式二：手动部署
```bash
npm run deploy
```

## 设置步骤

### 1. GitHub 仓库设置
1. 进入你的 GitHub 仓库
2. 点击 **Settings** 标签
3. 在左侧菜单中找到 **Pages**
4. 在 **Source** 部分，选择 **GitHub Actions**

### 2. 安装依赖
```bash
npm install
```

### 3. 本地测试
```bash
# 开发模式
npm run dev

# 构建测试
npm run build
npm run preview
```

### 4. 部署
推送代码到 main 分支即可自动部署：
```bash
git add .
git commit -m "Deploy to GitHub Pages"
git push origin main
```

## 访问地址
部署成功后，你的 PRISM 平台将可以通过以下地址访问：
```
https://[你的GitHub用户名].github.io/prism/
```

## 故障排除

### 构建失败
- 检查 package.json 中的依赖是否正确
- 确保所有 TypeScript 类型错误已解决

### 页面无法访问
- 确认 GitHub Pages 设置中的 Source 为 "GitHub Actions"
- 检查 Actions 标签页中的构建状态

### 路径问题
- 确保 vite.config.ts 中的 base 路径设置正确
- 如果仓库名不是 "prism"，需要修改 base 路径

## 注意事项
- 首次部署可能需要几分钟时间
- 确保你的 GitHub 仓库是公开的（或者有 GitHub Pro/Team 账户用于私有仓库 Pages）
- 修改后推送到 main 分支会触发自动重新部署
