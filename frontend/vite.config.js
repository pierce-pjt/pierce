import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // 👇 [여기 추가됨] 도커 및 윈도우 환경 필수 설정
  server: {
    host: '0.0.0.0', // 도커 밖에서 접속 허용
    port: 5173,
    watch: {
      usePolling: true, // 윈도우/도커 파일 변경 감지(핫 리로딩) 활성화
    },
    // 👇👇👇 여기가 핵심 수정 사항입니다!
    proxy: {
      '/api': {
        target: 'http://django:8000', 
        changeOrigin: true,
      },
      '/media': {
        target: 'http://django:8000',
        changeOrigin: true,
      }
    }
  }
})