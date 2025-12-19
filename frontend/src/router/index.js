import { createRouter, createWebHistory } from 'vue-router'

// 1. 뷰 컴포넌트들을 미리 import (Lazy Load 방식도 좋지만, 메인은 바로 로딩)
import LandingView from '../views/LandingView.vue'
import HomeView from '../views/HomeView.vue'
import StockDetailView from '../views/StockDetailView.vue'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingView,
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: HomeView,
  },
  {
    path: '/stock/:code',  // :code 부분이 변수처럼 동작 (예: /stock/005930)
    name: 'stock-detail',
    component: StockDetailView,
  },
  // 나머지 메뉴들 (뉴스, 커뮤니티, 마이페이지, 로그인 등)
  {
    path: '/news',
    name: 'news',
    component: () => import('../views/NewsView.vue'),
  },
  {
    path: '/news/:id', 
    name: 'news-detail',
    component: () => import('../views/NewsDetailView.vue'),
  },
  {
    path: '/community',
    name: 'community',
    component: () => import('../views/CommunityView.vue'),
  },
  // 👇 [추가] 커뮤니티 상세 페이지
  {
    path: '/community/:id',
    name: 'community-detail',
    component: () => import('../views/CommunityDetailView.vue'),
  },
  {
    path: '/my',
    name: 'mypage',
    component: () => import('../views/MyPageView.vue'),
  },
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
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router