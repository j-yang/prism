import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isFrontendOnly = process.env.VITE_BUILD_TARGET === 'frontend' || process.env.GITHUB_ACTIONS;

  return {
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
      }
      // 移除 API 代理配置，仅用于生产构建
    },
    // 确保public文件夹内容正确暴露
    publicDir: 'public',
    // 根据环境设置base路径
    base: isFrontendOnly ? '/prism/' : '/',
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      // 确保public文件夹内容复制到构建输出
      copyPublicDir: true,
      // 清理dist目录
      emptyOutDir: true,
      // 明确排除服务器相关文件
      rollupOptions: {
        external: isFrontendOnly ? [
          // 排除所有 Node.js 服务器相关模块
          'express',
          'multer',
          'ssh2-sftp-client',
          'cors',
          'dotenv',
          'fs',
          'path',
          'events'
        ] : [],
        output: {
          // 简化文件命名以避免路径问题
          manualChunks: undefined,
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name!.split('.')
            const extType = info[info.length - 1]
            if (/css/.test(extType)) {
              return `css/[name]-[hash].[ext]`
            }
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
              return `images/[name]-[hash].[ext]`
            }
            return `assets/[name]-[hash].[ext]`
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
  }
})
