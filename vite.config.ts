import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 处理自定义元素标签
          isCustomElement: (tag) => tag.includes('-')
        }
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    open: true,
    // 确保静态文件正确服务
    fs: {
      strict: false
    },
    // 添加代理配置
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  // 确保public文件夹内容正确暴露
  publicDir: 'public',
  // GitHub Pages部署配置 - 基于分支部署
  base: process.env.NODE_ENV === 'production' ? '/prism/' : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    // 确保public文件夹内容复制到构建输出
    copyPublicDir: true
  }
})
