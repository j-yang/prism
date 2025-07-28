import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
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
      fs: {
        strict: false
      }
    },
    publicDir: 'public',
    // 修复base路径 - 对于GitHub Pages，仓库名需要匹配
    base: isFrontendOnly ? '/prism/' : '/',
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: false,
      copyPublicDir: true,
      emptyOutDir: true,
      rollupOptions: {
        external: isFrontendOnly ? [
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
          manualChunks: undefined,
          // 简化文件命名，避免特殊字符
          chunkFileNames: 'js/[name].[hash].js',
          entryFileNames: 'js/[name].[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name!.split('.')
            const extType = info[info.length - 1]
            if (/css/.test(extType)) {
              return `css/[name].[hash].[ext]`
            }
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
              return `images/[name].[hash].[ext]`
            }
            return `assets/[name].[hash].[ext]`
          }
        }
      },
      chunkSizeWarningLimit: 1000,
      minify: isProduction ? 'terser' : false,
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true
        }
      } : undefined
    }
  }
})
