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
  // Fix base path for GitHub Pages - always use /prism/ for production
  base: process.env.NODE_ENV === 'production' ? '/prism/' : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    // 确保public文件夹内容复制到构建输出
    copyPublicDir: true,
    // 清理dist目录
    emptyOutDir: true,
    // 优化构建配置以减少文件大小和改善加载性能
    rollupOptions: {
      output: {
        // 简化文件命名，避免复杂的分包导致404
        manualChunks: undefined,
        chunkFileNames: 'assets/js/[name].[hash].js',
        entryFileNames: 'assets/js/[name].[hash].js',
        assetFileNames: (assetInfo) => {
          if (!assetInfo.name) return 'assets/[name].[hash].[ext]'

          if (/\.(css)$/.test(assetInfo.name)) {
            return 'assets/css/[name].[hash].[ext]'
          }
          if (/\.(png|jpe?g|gif|svg|ico|webp)$/.test(assetInfo.name)) {
            return 'assets/images/[name].[hash].[ext]'
          }
          return 'assets/[name].[hash].[ext]'
        }
      }
    },
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    // 启用代码压缩
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 移除console.log
        drop_debugger: true // 移除debugger
      }
    }
  }
})
