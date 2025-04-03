/// <reference types="vitest" />
/// <reference types="vite/client" />
/// <reference types="node" />
// @ts-ignore
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
// @ts-ignore
import AutoImport from 'unplugin-auto-import/vite';
// @ts-ignore
import Components from 'unplugin-vue-components/vite';
// @ts-ignore
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import path from 'path';
// @ts-ignore
import type { Connect } from 'vite';

// 自定义中间件处理模块加载问题
// @ts-ignore
const handleWorkerRequests: Connect.NextHandleFunction = (req, res, next) => {
  if (req.url && req.url.includes('/workers/')) {
    console.log('拦截workers请求:', req.url);
    res.setHeader('Content-Type', 'application/javascript');
    res.end('export default {}');
    return;
  }
  next();
};

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
    // 添加自定义插件处理Web Worker请求
    {
      name: 'handle-worker-requests',
      configureServer(server) {
        server.middlewares.use(handleWorkerRequests);
      }
    }
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
    dedupe: ['crypto-js'],
  },
  optimizeDeps: {
    include: [
      'crypto-js',
      'element-plus',
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'lodash-es',
      '@vueuse/core',
    ],
    exclude: [],
  },
  server: {
    host: '0.0.0.0',
    port: 5176,
    cors: {
      origin: '*',
      credentials: true,
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('代理错误:', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('代理请求:', req.url);
            const host = req.headers.host || 'freight.test:8000';
            proxyReq.setHeader('Host', host);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('代理响应:', req.url, proxyRes.statusCode);
          });
        }
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/service-worker.js': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        headers: {
          'Content-Type': 'application/javascript',
        },
      },
      '/token-*': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        secure: false,
        changeOrigin: true,
      },
      '/src/workers': {
        target: 'http://127.0.0.1:5174',
        changeOrigin: true,
        bypass(req) {
          if (req.headers.accept && req.headers.accept.includes('text/html')) {
            console.log('返回空的JavaScript模块');
            req.headers['Content-Type'] = 'application/javascript';
            return '/empty-module.js';
          }
        },
      },
    },
  },
  define: {
    'process.env': {
      NODE_ENV: JSON.stringify(process.env.NODE_ENV),
    },
    'process.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || 'https://your-api-domain.ngrok.dev'),
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
