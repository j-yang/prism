# 基于分支的GitHub Pages部署指南

## 部署方式：gh-pages分支

这种方式通过创建一个专门的`gh-pages`分支来存放构建后的静态文件，比GitHub Actions更简单稳定。

## 部署步骤

### 1. 安装依赖
```bash
npm install
```

### 2. 构建并部署
```bash
npm run deploy
```

这个命令会：
- 构建项目到 `dist` 目录
- 将 `dist` 内容推送到 `gh-pages` 分支
- 自动创建并切换分支

### 3. GitHub Pages设置
1. 进入GitHub仓库
2. Settings → Pages
3. Source 选择 "Deploy from a branch"
4. Branch 选择 "gh-pages" 
5. Folder 选择 "/ (root)"
6. 点击 Save

## 访问地址
部署成功后访问：
```
https://[你的用户名].github.io/prism/
```

## 优势
- 更简单，不需要配置GitHub Actions
- 更稳定，避免Actions权限问题
- 可以本地控制部署时机
- 容易排查问题

## 常用命令
```bash
# 开发模式
npm run dev

# 构建测试
npm run build
npm run preview

# 部署到GitHub Pages
npm run deploy
```

## 注意事项
- 确保仓库名与vite.config.ts中的base路径一致
- 首次部署需要几分钟生效
- 每次想要更新网站时，运行 `npm run deploy`
