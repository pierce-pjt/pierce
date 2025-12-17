<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logoImg from '@/assets/logo.png' 

const route = useRoute()
const router = useRouter() // 1. 라우터 인스턴스 생성
const authStore = useAuthStore()
const isActive = (name) => route.name === name

// 2. 마이페이지 이동 함수
const goToMyPage = () => {
  router.push({ name: 'mypage' })
}

onMounted(() => {
  authStore.fetchUser()
})
</script>

<template>
  <div class="app">
    <header class="nav-bar">
      <div class="nav-inner">
        <RouterLink :to="{ name: 'landing' }" class="logo-link">
          <img :src="logoImg" alt="BackLoop" class="logo-image" />
        </RouterLink>

        <nav class="nav-menu">
          <RouterLink :to="{ name: 'dashboard' }" class="nav-item" :class="{ active: isActive('dashboard') }">
            홈
          </RouterLink>
          <RouterLink :to="{ name: 'news' }" class="nav-item" :class="{ active: isActive('news') }">
            뉴스
          </RouterLink>
          <RouterLink :to="{ name: 'community' }" class="nav-item" :class="{ active: isActive('community') }">
            커뮤니티
          </RouterLink>
          <RouterLink :to="{ name: 'mypage' }" class="nav-item" :class="{ active: isActive('mypage') }">
            마이
          </RouterLink>
        </nav>

        <div class="auth-area">
          <template v-if="authStore.isAuthenticated && authStore.user">
            <div class="user-profile" @click="goToMyPage">
              <img :src="authStore.user.profile_image_url || '/default-profile.png'" class="user-avatar" />
              <span class="user-name">{{ authStore.user.nickname }}</span>
              <button @click.stop="authStore.logout" class="logout-link">로그아웃</button>
            </div>
          </template>
          <template v-else>
            <RouterLink :to="{ name: 'login' }">
              <button class="login-btn">로그인</button>
            </RouterLink>
          </template>
        </div>
      </div>
    </header>

    <main :class="route.name === 'landing' ? 'main-full' : 'main-area'">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app { min-height: 100vh; background: #050711; color: #f5f5f7; font-family: system-ui, sans-serif; }

/* 네비게이션 바 */
.nav-bar { position: sticky; top: 0; z-index: 20; backdrop-filter: blur(14px); background: rgba(5,7,17,0.8); border-bottom: 1px solid rgba(255,255,255,0.05); }
.nav-inner { max-width: 1120px; margin: 0 auto; padding: 0 20px; height: 64px; display: flex; align-items: center; justify-content: space-between; }
.logo-image { height: 32px; display: block; }

/* 메뉴 */
.nav-menu { display: flex; gap: 24px; font-weight: 500; font-size: 15px; }
.nav-item { color: #9ca3af; text-decoration: none; padding: 6px 0; position: relative; }
.nav-item:hover, .nav-item.active { color: #fff; }
.nav-item.active::after { content: ''; position: absolute; bottom: -21px; left: -4px; right: -4px; height: 2px; background: #3b82f6; }

/* 로그인 버튼 */
.login-btn { background: #2563eb; color: white; border: none; padding: 7px 18px; border-radius: 99px; font-weight: 600; cursor: pointer; }

/* 프로필 영역: 커서 포인터 추가 */
.user-profile { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.user-avatar { width: 32px; height: 32px; border-radius: 50%; border: 1px solid #3b82f6; }
.user-name { font-weight: 600; font-size: 14px; }
.logout-link { background: none; border: none; color: #9ca3af; cursor: pointer; font-size: 13px; }
.logout-link:hover { color: #ef4444; }

/* 메인 영역 스타일 */
.main-area { max-width: 1120px; margin: 0 auto; padding: 32px 20px 60px; }
.main-full { width: 100%; padding: 0; margin: 0; }
</style>