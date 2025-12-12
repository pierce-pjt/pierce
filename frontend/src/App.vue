<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth' // 1. Auth 스토어 import

// ❗ 로고 이미지 (경로 확인 필요)
import logoImg from '@/assets/logo.png' 

const route = useRoute()
const authStore = useAuthStore() // 2. 스토어 사용 설정

const isActive = (name) => route.name === name

// 3. 앱이 시작될 때(새로고침 포함) 내 정보 가져오기 -> 로그인 유지
onMounted(() => {
  authStore.fetchUser()
})
</script>

<template>
  <div class="app">
    <header class="nav-bar">
      <div class="nav-inner">
        <RouterLink :to="{ name: 'home' }" class="logo-link">
          <img :src="logoImg" alt="BackLoop" class="logo-image" />
        </RouterLink>

        <nav class="nav-menu">
          <RouterLink
            :to="{ name: 'home' }"
            class="nav-item"
            :class="{ active: isActive('home') }"
          >
            홈
          </RouterLink>
          <RouterLink
            :to="{ name: 'news' }"
            class="nav-item"
            :class="{ active: isActive('news') }"
          >
            뉴스
          </RouterLink>
          <RouterLink
            :to="{ name: 'community' }"
            class="nav-item"
            :class="{ active: isActive('community') }"
          >
            커뮤니티
          </RouterLink>
          <RouterLink
            :to="{ name: 'mypage' }"
            class="nav-item"
            :class="{ active: isActive('mypage') }"
          >
            마이
          </RouterLink>
        </nav>

        <div class="auth-area">
          <template v-if="authStore.isAuthenticated && authStore.user">
            <div class="user-profile">
              <img 
                v-if="authStore.user.profile_image_url" 
                :src="authStore.user.profile_image_url" 
                class="user-avatar" 
                alt="Profile"
              />
              <span class="user-name">{{ authStore.user.nickname }}</span>
              <button @click="authStore.logout" class="logout-link">
                로그아웃
              </button>
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

    <main class="main-area">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: #050711;
  color: #f5f5f7;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.nav-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(14px);
  background: linear-gradient(to bottom, rgba(5, 7, 17, 0.95), rgba(5, 7, 17, 0.7));
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0 20px; 
  height: 64px;    
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 로고 스타일 */
.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  padding: 4px 0;
}

.logo-image {
  height: 40px; 
  width: auto;
  display: block;
  margin: 0;
}

/* 네비게이션 메뉴 */
.nav-menu {
  display: flex;
  gap: 24px;
  font-size: 15px; 
  font-weight: 500;
}

.nav-item {
  position: relative;
  padding: 6px 0; 
  color: #9ca3af;
  text-decoration: none;
  transition: color 0.2s ease;
}

.nav-item:hover {
  color: #ffffff;
}

.nav-item.active {
  color: #ffffff;
  font-weight: 600;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  left: -4px;
  right: -4px;
  bottom: -21px; 
  height: 2px;
  border-radius: 999px;
  background: #3b82f6; 
  box-shadow: 0 -1px 4px rgba(59, 130, 246, 0.5);
}

/* --- 로그인/유저 프로필 스타일 --- */

.auth-area {
  display: flex;
  align-items: center;
  min-width: 100px; /* 로딩 시 레이아웃 흔들림 방지 */
  justify-content: flex-end;
}

/* 로그인 버튼 */
.login-btn {
  padding: 7px 18px;
  border-radius: 999px;
  border: none;
  background: #2563eb;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.login-btn:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.login-btn:active {
  transform: translateY(0);
}

/* 유저 프로필 영역 */
.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #3b82f6;
  object-fit: cover;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #f5f5f7;
}

.logout-link {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.2s;
}

.logout-link:hover {
  color: #ef4444; /* 로그아웃은 빨간색 호버 */
}

.main-area {
  max-width: 1120px;
  margin: 0 auto;
  padding: 32px 20px 60px;
}
</style>