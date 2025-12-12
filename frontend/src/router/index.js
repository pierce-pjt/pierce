// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/news',
    name: 'news',
    // 💡 lazy-loaded: 방문할 때 로드됨
    component: () => import('../views/NewsView.vue'),
  },
  {
    path: '/community',
    name: 'community',
    component: () => import('../views/CommunityView.vue'),
  },
  {
    path: '/my',
    name: 'mypage',
    component: () => import('../views/MyPageView.vue'),
  },
  // 👇 로그인 및 회원가입 라우트 추가
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/signup',
    name: 'signup',
    component: () => import('../views/SignupView.vue'),
  },
]

const router = createRouter({
  // Vite 환경 변수 사용 (배포 시 경로 문제 방지)
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router