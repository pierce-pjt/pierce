// frontend/src/router/index.js
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
    // 나중에 만들 예정
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
