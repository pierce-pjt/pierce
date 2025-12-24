<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import logoImg from '@/assets/logo.png' 

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isActive = (name) => route.name === name

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
            HOME
          </RouterLink>
          <RouterLink :to="{ name: 'news' }" class="nav-item" :class="{ active: isActive('news') }">
            NEWS
          </RouterLink>
          <RouterLink :to="{ name: 'community' }" class="nav-item" :class="{ active: isActive('community') }">
            COMMUNITY
          </RouterLink>
          <RouterLink :to="{ name: 'mypage' }" class="nav-item" :class="{ active: isActive('mypage') }">
            MYPAGE
          </RouterLink>
        </nav>

        <div class="auth-area">
          <template v-if="authStore.isAuthenticated && authStore.user">
            <div class="user-profile" @click="goToMyPage">
              <img :src="authStore.user.profile_image_url || '/default-profile.png'" class="user-avatar" />
              <span class="user-name">{{ authStore.user.nickname }}</span>
              <button @click.stop="authStore.logout" class="logout-link">LOGOUT</button>
            </div>
          </template>
          <template v-else>
            <RouterLink :to="{ name: 'login' }">
              <button class="login-btn">LOGIN</button>
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
.app { 
  min-height: 100vh; 
  background: #17171C; 
  color: #f5f5f7; 
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* 네비게이션 바 */
.nav-bar { 
  position: sticky; 
  top: 0; 
  z-index: 20; 
  backdrop-filter: blur(14px); 
  background: #17171C(5,7,17,0.8); 
  border-bottom: 1px solid rgba(255,255,255,0.05); 
}

.nav-inner { 
  max-width: 2000px; 
  margin: 0 auto; 
  padding: 0 20px; 
  height: 68px;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 20px;
}

.logo-link {
  justify-self: start;
}

.logo-image { 
  height: 64px; 
  display: block; 
}

/* 메뉴 - 정중앙 배치 */
.nav-menu { 
  display: flex; 
  gap: 32px;
  font-weight: 600;
  font-size: 16px;
  font-family: 'Noto Sans KR', sans-serif;
  justify-self: center;
}

.nav-item { 
  color: #9ca3af; 
  text-decoration: none; 
  padding: 8px 0; 
  position: relative;
  transition: color 0.2s;
  white-space: nowrap;
}

.nav-item:hover, .nav-item.active { 
  color: #fff; 
}

.nav-item.active::after { 
  content: ''; 
  position: absolute; 
  bottom: -22px; 
  left: -4px; 
  right: -4px; 
  height: 2px; 
  background: #3b82f6; 
}

/* 인증 영역 - 오른쪽 끝 배치 */
.auth-area {
  justify-self: end;
}

/* 로그인 버튼 */
.login-btn { 
  background: #2563eb; 
  color: white; 
  border: none; 
  padding: 9px 20px; 
  border-radius: 99px; 
  font-weight: 600; 
  font-size: 14px;
  cursor: pointer;
  font-family: 'Noto Sans KR', sans-serif;
  transition: background 0.2s;
}

.login-btn:hover {
  background: #1d4ed8;
}

/* 프로필 영역 */
.user-profile { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 12px;
  transition: background 0.2s;
}

.user-profile:hover {
  background: rgba(255,255,255,0.05);
}

.user-avatar { 
  width: 36px; 
  height: 36px; 
  border-radius: 50%; 
  border: 2px solid #3b82f6; 
}

.user-name { 
  font-weight: 600; 
  font-size: 15px;
  font-family: 'Noto Sans KR', sans-serif;
}

.logout-link { 
  background: none; 
  border: none; 
  color: #9ca3af; 
  cursor: pointer; 
  font-size: 14px;
  font-family: 'Noto Sans KR', sans-serif;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.logout-link:hover { 
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

/* 메인 영역 스타일 */
.main-area { 
  max-width: 2000px; 
  margin: 0 auto; 
  padding: 32px 20px 60px; 
}

.main-full { 
  width: 100%; 
  padding: 0; 
  margin: 0; 
}
</style>

<style>
/* 스크롤바 공간 강제 확보 */
html, body, .v-application, .v-application__wrap {
  overflow-y: scroll !important; 
}

/* 폰트 통일 */
:root, body, .v-application {
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
  background-color: #121212;
}

/* 스크롤바 디자인 */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1e1e1e; }
::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #777; }
</style>