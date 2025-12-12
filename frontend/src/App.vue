<script setup>
import { RouterView } from 'vue-router'
</script>

<template>
  <v-app>
    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>

<style>
/* 👇 [핵심 수정] html뿐만 아니라 Vuetify의 메인 래퍼(wrapper)까지 스크롤바 공간 강제 확보 */
html, body, .v-application, .v-application__wrap {
  overflow-y: scroll !important; 
}

/* 폰트 및 배경 설정 */
:root, body, .v-application {
  font-family: 'Noto Sans KR', sans-serif !important;
  background-color: #121212; /* 배경색 유지 */
}

/* (선택사항) 스크롤바 디자인 */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1e1e1e; }
::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #777; }
</style>