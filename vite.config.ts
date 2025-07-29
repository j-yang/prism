import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
  const isFrontendOnly = process.env.VITE_BUILD_TARGET === 'frontend' || process.env.GITHUB_ACTIONS;

  // Determine base path - use repository name for GitHub Pages
  const baseUrl = isFrontendOnly ? '/prism/' : '/';

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
      },
      // Add proxy for development to handle API calls
      proxy: isFrontendOnly ? {} : {
        '/api': {
          target: 'http://localhost:3001',
          changeOrigin: true,
          secure: false
        }
      }
    },
    publicDir: 'public',
    base: baseUrl,
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
          // Ensure proper asset naming for GitHub Pages
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name!.split('.')
            const extType = info[info.length - 1]
            if (/css/.test(extType)) {
              return `assets/css/[name]-[hash].[ext]`
            }
            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
              return `assets/images/[name]-[hash].[ext]`
            }
            return `assets/[name]-[hash].[ext]`
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
    },
    // Add define to pass environment variables to the app
    define: {
      __IS_GITHUB_PAGES__: JSON.stringify(isFrontendOnly),
      __BASE_URL__: JSON.stringify(baseUrl)
    }
  }
})
