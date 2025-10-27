# PRISM 项目文件结构说明

本文档详细介绍 PRISM (Platform for Research Infrastructure Smart Manufacturing) 项目的文件和目录组织结构。

## 📋 目录

- [总体结构](#总体结构)
- [核心目录详解](#核心目录详解)
- [配置文件说明](#配置文件说明)
- [文件命名规范](#文件命名规范)
- [技术栈依赖](#技术栈依赖)

## 总体结构

```
prism/
├── .github/                      # GitHub 相关配置
│   ├── agents/                   # GitHub Copilot 代理配置
│   └── workflows/                # GitHub Actions 工作流
│
├── .vscode/                      # VS Code 编辑器配置
│   └── settings.json             # 项目特定的编辑器设置
│
├── public/                       # 静态资源文件（不经过编译）
│   ├── references/               # 参考文档和示例
│   │   └── sdtm/                 # SDTM 相关参考资料
│   ├── templates/                # 预置 SAS 代码模板
│   │   ├── adam production template.sas      # ADaM 生产环境模板
│   │   ├── adam validation template.sas      # ADaM 验证环境模板
│   │   ├── sdtm production template.sas      # SDTM 生产环境模板
│   │   ├── sdtm validation template.sas      # SDTM 验证环境模板
│   │   ├── tlf_dev_template_code.sas         # TLF 开发模板
│   │   └── tlf_val_template_code.sas         # TLF 验证模板
│   ├── prism-logo.svg            # 项目 Logo
│   ├── vite.svg                  # Vite 图标
│   ├── .nojekyll                 # GitHub Pages 配置（禁用 Jekyll）
│   └── 404.html                  # 404 错误页面
│
├── server/                       # 后端服务器（Node.js + Express）
│   ├── uploads/                  # 文件上传临时存储目录
│   ├── server.js                 # Express 服务器主入口
│   ├── package.json              # 服务器端依赖配置
│   ├── package-lock.json         # 服务器端依赖锁定文件
│   └── .env                      # 服务器环境变量配置（不提交到版本控制）
│
├── src/                          # 前端源代码（Vue 3 + TypeScript）
│   ├── assets/                   # 资源文件
│   │   ├── main.css              # 全局样式文件
│   │   └── vue.svg               # Vue Logo
│   │
│   ├── components/               # Vue 组件库
│   │   ├── TemplateManager.vue              # 模板管理器主组件
│   │   ├── SASCodeEditor.vue                # SAS 代码编辑器组件
│   │   ├── ServerConnectionDialog.vue       # 服务器连接对话框
│   │   ├── ServerFileBrowser.vue            # 服务器文件浏览器
│   │   ├── TemplateSelectionDialog.vue      # 模板选择对话框
│   │   └── FileConflictDialog.vue           # 文件冲突处理对话框
│   │
│   ├── services/                 # 业务逻辑服务层
│   │   ├── types/                # TypeScript 类型定义
│   │   │   ├── adam.d.ts         # ADaM 数据结构类型定义
│   │   │   └── jszip.d.ts        # JSZip 库类型定义
│   │   ├── ExcelProcessor.ts                # Excel 文件解析处理服务
│   │   ├── ProgramGenerator.ts              # SAS 程序生成核心服务
│   │   ├── ReferenceTemplateService.ts      # 参考模板管理服务
│   │   ├── ServerFileManager.ts             # 服务器文件操作管理
│   │   ├── MockServerAPI.ts                 # 模拟服务器 API（用于开发测试）
│   │   └── TemplateStorageService.ts        # 模板本地存储服务
│   │
│   ├── stores/                   # 状态管理（Pinia）
│   │   └── templateStore.ts                 # 模板全局状态管理
│   │
│   ├── utils/                    # 工具函数
│   │   └── environment.ts                   # 环境配置和变量管理
│   │
│   ├── App.vue                   # Vue 根组件
│   ├── main.ts                   # 应用程序主入口
│   └── vite-env.d.ts             # Vite 环境类型定义
│
├── index.html                    # HTML 入口文件
├── demo.html                     # 演示页面
│
├── package.json                  # 前端项目依赖和脚本配置
├── package-lock.json             # 前端依赖版本锁定文件
│
├── vite.config.ts                # Vite 构建工具配置
├── tsconfig.json                 # TypeScript 基础配置
├── tsconfig.app.json             # TypeScript 应用代码配置
├── tsconfig.node.json            # TypeScript Node.js 环境配置
│
├── .gitignore                    # Git 版本控制忽略文件配置
│
├── README.md                     # 项目主说明文档
├── CHANGELOG.md                  # 版本变更历史记录
├── DEPLOYMENT.md                 # 部署指南
├── PRODUCTION_DEPLOYMENT.md      # 生产环境部署指南
├── BRANCH_DEPLOYMENT.md          # 分支部署指南
├── DEPLOYMENT_TROUBLESHOOTING.md # 部署故障排除指南
├── GITHUB_PAGES_FIX.md           # GitHub Pages 修复指南
├── TROUBLESHOOTING.md            # 常见问题故障排除
└── RELEASE_NOTES.md              # 版本发布说明
```

## 核心目录详解

### 1. `/src` - 前端源代码目录

这是项目的核心目录，包含所有前端应用的源代码。采用 Vue 3 + TypeScript 技术栈开发。

#### `/src/components` - Vue 组件库

存放所有可重用的 Vue 组件，每个组件负责特定的 UI 功能：

- **TemplateManager.vue** - 模板管理器的主组件
  - 提供模板的创建、编辑、删除功能
  - 管理用户自定义模板和系统预置模板
  - 支持模板的导入和导出

- **SASCodeEditor.vue** - SAS 代码编辑器
  - 提供语法高亮的代码编辑功能
  - 支持代码格式化和验证
  - 实时预览和编辑体验

- **ServerConnectionDialog.vue** - 服务器连接对话框
  - 管理 SFTP 服务器连接配置
  - 处理连接认证和验证
  - 保存连接配置信息

- **ServerFileBrowser.vue** - 服务器文件浏览器
  - 浏览远程服务器文件系统
  - 支持文件上传和下载
  - 提供文件管理操作界面

- **TemplateSelectionDialog.vue** - 模板选择对话框
  - 在程序生成时选择合适的模板
  - 预览模板内容和说明
  - 支持按类型筛选模板

- **FileConflictDialog.vue** - 文件冲突处理对话框
  - 处理文件名冲突情况
  - 提供覆盖、重命名等解决方案
  - 批量处理冲突文件

#### `/src/services` - 业务逻辑服务层

封装核心业务逻辑，与 UI 层分离，便于测试和维护：

- **ExcelProcessor.ts** - Excel 文件解析服务
  - 读取和解析 Excel 文件（.xlsx, .xls）
  - 提取元数据信息（数据集名称、程序名称等）
  - 验证数据格式和完整性
  - 支持多工作表解析

- **ProgramGenerator.ts** - 程序生成核心服务
  - 根据模板和元数据生成 SAS 程序
  - 实现变量替换引擎（如 {{DATASET_NAME}}）
  - 批量生成 Production 和 Validation 程序
  - 打包生成的程序为 ZIP 文件

- **TemplateStorageService.ts** - 模板存储服务
  - 使用浏览器 LocalStorage 存储模板
  - 提供模板的 CRUD 操作
  - 管理模板版本和元数据
  - 模板数据的序列化和反序列化

- **ReferenceTemplateService.ts** - 参考模板服务
  - 加载系统预置的参考模板
  - 从 `/public/templates` 目录读取模板文件
  - 提供模板的分类和检索功能

- **ServerFileManager.ts** - 服务器文件管理服务
  - 与后端 API 通信管理服务器文件
  - 实现文件的上传、下载、删除操作
  - 处理 SFTP 连接和文件传输

- **MockServerAPI.ts** - 模拟服务器 API
  - 开发和测试时使用的模拟 API
  - 模拟服务器响应和数据
  - 无需真实后端即可开发前端功能

#### `/src/services/types` - TypeScript 类型定义

存放项目中使用的 TypeScript 类型声明文件：

- **adam.d.ts** - ADaM (Analysis Data Model) 数据结构类型
  - 定义 ADaM 数据集的接口
  - 元数据字段类型定义
  - 程序生成相关的类型

- **jszip.d.ts** - JSZip 库的类型定义
  - 扩展 JSZip 库的类型声明
  - 确保类型安全的 ZIP 文件操作

#### `/src/stores` - 状态管理

使用 Pinia 进行全局状态管理：

- **templateStore.ts** - 模板状态管理 Store
  - 管理当前加载的模板列表
  - 追踪当前选中的模板
  - 提供模板相关的 actions 和 getters
  - 与 TemplateStorageService 协同工作

#### `/src/utils` - 工具函数

通用工具函数和辅助方法：

- **environment.ts** - 环境配置工具
  - 检测运行环境（开发/生产）
  - 提供环境特定的配置
  - 管理环境变量访问

### 2. `/public` - 静态资源目录

存放不需要经过 Vite 编译处理的静态文件，这些文件会被直接复制到构建输出目录。

#### `/public/templates` - 预置代码模板

系统预装的 SAS 程序模板：

- **adam production template.sas** - ADaM 数据集生产环境程序模板
- **adam validation template.sas** - ADaM 数据集验证程序模板
- **sdtm production template.sas** - SDTM 数据集生产环境程序模板
- **sdtm validation template.sas** - SDTM 数据集验证程序模板
- **tlf_dev_template_code.sas** - TLF (Tables, Listings, Figures) 开发模板
- **tlf_val_template_code.sas** - TLF 验证模板

这些模板使用变量占位符系统，如：
```sas
/* 常用变量占位符 */
{{DATASET_NAME}}     /* 数据集名称 */
{{PROGRAM_NAME}}     /* 程序文件名 */
{{PROGRAMMER}}       /* 程序员姓名 */
{{OUTPUT_TYPE}}      /* 输出类型 */
{{CURRENT_DATE}}     /* 当前日期 */
{{TIMESTAMP}}        /* 时间戳 */
```

#### `/public/references` - 参考文档

示例文件、使用指南和最佳实践文档：

- **sdtm/** - SDTM 相关参考资料和示例

### 3. `/server` - 后端服务目录

基于 Node.js + Express.js 的后端服务，提供文件上传、SFTP 连接等功能。

#### 主要文件

- **server.js** - Express 服务器主入口文件
  - 提供 RESTful API 接口
  - 文件上传处理
  - SFTP 连接管理
  - 文件浏览和操作接口
  - 跨域请求处理（CORS）

- **package.json** - 服务器端依赖配置
  - Express 框架
  - Multer（文件上传中间件）
  - SSH2-SFTP-Client（SFTP 客户端）
  - 其他服务器端依赖

- **.env** - 环境变量配置文件（不提交到版本控制）
  - 服务器端口配置
  - SFTP 连接凭证
  - 其他敏感配置信息

#### `/server/uploads` - 上传临时目录

存储通过 API 上传的临时文件，具有自动清理机制。

## 配置文件说明

### 构建和编译配置

#### `vite.config.ts` - Vite 构建工具配置

```typescript
// 主要配置项
- plugins: [vue()]              // Vue 3 插件
- server.port: 5173            // 开发服务器端口
- server.open: true            // 自动打开浏览器
- build.outDir: 'dist'         // 构建输出目录
- base: '/prism/'              // 基础路径（用于 GitHub Pages）
```

#### TypeScript 配置文件

- **tsconfig.json** - TypeScript 基础配置
  - 编译器基础选项
  - 引用其他配置文件

- **tsconfig.app.json** - 应用代码配置
  - 前端应用代码的编译选项
  - 包含 `src/` 目录
  - 排除测试文件

- **tsconfig.node.json** - Node.js 环境配置
  - 用于 Vite 配置文件的编译
  - Node.js 环境类型支持

### 项目配置

#### `package.json` - 前端项目配置

主要脚本命令：

```json
{
  "scripts": {
    "dev": "并发运行前端和后端开发服务器",
    "dev:client": "启动 Vite 前端开发服务器",
    "dev:server": "启动 Express 后端服务器",
    "build": "构建生产版本",
    "build:frontend-only": "仅构建前端（用于 GitHub Pages）",
    "preview": "预览构建结果",
    "type-check": "TypeScript 类型检查",
    "deploy": "部署到 GitHub Pages",
    "deploy:force": "强制部署到 GitHub Pages"
  }
}
```

主要依赖：

- **运行时依赖**
  - vue (^3.5.17) - Vue 3 框架
  - pinia (^3.0.3) - 状态管理
  - vue-router (^4.5.1) - 路由管理
  - xlsx (^0.18.5) - Excel 文件处理
  - jszip (^3.10.1) - ZIP 文件生成
  - file-saver (^2.0.5) - 文件下载

- **开发依赖**
  - @vitejs/plugin-vue - Vite Vue 插件
  - typescript - TypeScript 编译器
  - vue-tsc - Vue TypeScript 编译器
  - gh-pages - GitHub Pages 部署工具

## 文件命名规范

### Vue 组件命名

- 使用 **PascalCase**（帕斯卡命名法）
- 文件名与组件名保持一致
- 示例：`TemplateManager.vue`, `SASCodeEditor.vue`

### 服务文件命名

- 使用 **PascalCase** + 描述性后缀
- 一个文件对应一个主要服务类
- 示例：`ExcelProcessor.ts`, `ProgramGenerator.ts`

### 类型定义文件

- 使用 `.d.ts` 扩展名
- 存放在 `src/services/types/` 目录
- 示例：`adam.d.ts`, `jszip.d.ts`

### 配置文件

- 使用小写字母和连字符
- 示例：`vite.config.ts`, `tsconfig.json`

## 技术栈依赖

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5.17 | 渐进式 JavaScript 框架 |
| TypeScript | 5.7.2 | JavaScript 的超集，提供类型系统 |
| Vite | 5.4.0 | 下一代前端构建工具 |
| Pinia | 3.0.3 | Vue 官方状态管理库 |
| Vue Router | 4.5.1 | Vue 官方路由管理器 |

### 数据处理库

| 库 | 版本 | 用途 |
|------|------|------|
| SheetJS (xlsx) | 0.18.5 | Excel 文件读取和解析 |
| JSZip | 3.10.1 | ZIP 文件生成和处理 |
| FileSaver | 2.0.5 | 客户端文件保存 |

### 后端技术栈

| 技术 | 用途 |
|------|------|
| Node.js | 服务器运行环境 |
| Express.js | Web 应用框架 |
| Multer | 文件上传中间件 |
| SSH2-SFTP-Client | SFTP 文件传输 |

## 开发工作流

### 开发环境启动

```bash
# 安装依赖
npm install

# 启动开发服务器（前端 + 后端）
npm run dev

# 仅启动前端
npm run dev:client

# 仅启动后端
npm run dev:server
```

### 构建流程

```bash
# 类型检查
npm run type-check

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

### 部署流程

```bash
# 部署到 GitHub Pages
npm run deploy

# 强制部署（覆盖现有部署）
npm run deploy:force
```

## 项目特点

### 模块化架构

- 清晰的目录结构和职责分离
- 组件化开发，高度可重用
- 服务层独立，易于测试和维护

### 类型安全

- 全面使用 TypeScript
- 严格的类型检查
- 完善的类型定义

### 现代化工具链

- Vite 快速开发和构建
- Vue 3 Composition API
- Pinia 轻量级状态管理

### 开发友好

- 热模块替换（HMR）
- 详细的代码注释
- 完善的文档体系

## 相关文档

- [README.md](./README.md) - 项目主文档
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 部署指南
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - 故障排除
- [CHANGELOG.md](./CHANGELOG.md) - 版本变更历史

---

**文档最后更新时间**: 2025-10-27

如有问题或建议，欢迎提交 [GitHub Issue](https://github.com/j-yang/prism/issues)。
