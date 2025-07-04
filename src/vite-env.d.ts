/// <reference types="vite/client" />

// 声明 Vue 文件模块
declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

// 补充 Vite 环境变量类型
interface ImportMetaEnv {
    readonly VITE_APP_TITLE: string
    readonly VITE_API_BASE: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
q
