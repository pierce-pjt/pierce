import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue' // 혹은 LoginView.vue

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/news',
    name: 'news',
    // 이제 NewsView가 만들어졌으니 주석 제거
    component: () => import('../views/NewsView.vue'),
  },
  // 👇 [추가] 뉴스 상세 페이지 (ID를 받아서 이동)
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
  {
    path: '/my',
    name: 'mypage',
    component: () => import('../views/MyPageView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router