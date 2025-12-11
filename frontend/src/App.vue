<!-- frontend/src/App.vue -->
<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()

const isActive = (name) => route.name === name
</script>

<template>
  <div class="app">
    <!-- 상단 네비게이션 -->
    <header class="nav-bar">
      <div class="nav-inner">
        <!-- 로고 영역 -->
        <div class="logo">
          <span class="logo-icon">📈</span>
          <span class="logo-text">주식코치</span>
        </div>

        <!-- 메뉴 -->
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

        <!-- 로그인 버튼 (나중에 실제 로그인 연동) -->
        <button class="login-btn">
          로그인
        </button>
      </div>
    </header>

    <!-- 각 페이지 내용 -->
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
  padding: 12px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 20px;
}

.logo-text {
  font-weight: 700;
  font-size: 18px;
}

.nav-menu {
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.nav-item {
  position: relative;
  padding: 6px 4px;
  color: #b3b7c6;
  text-decoration: none;
  transition: color 0.15s ease;
}

.nav-item:hover {
  color: #ffffff;
}

.nav-item.active {
  color: #ffffff;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, #5b8dff, #9b5bff);
}

.login-btn {
  padding: 6px 16px;
  border-radius: 999px;
  border: none;
  background: #2563eb;
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 0 0 1px rgba(37, 99, 235, 0.4), 0 8px 18px rgba(37, 99, 235, 0.45);
  transition: transform 0.1s ease, box-shadow 0.1s ease, background 0.1s ease;
}

.login-btn:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.6);
}

.login-btn:active {
  transform: translateY(0);
  box-shadow: 0 6px 14px rgba(37, 99, 235, 0.4);
}

.main-area {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px 20px 40px;
}
</style>
