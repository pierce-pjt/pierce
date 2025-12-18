<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const nickname = ref('')
const password = ref('')

const handleLogin = async () => {
  if (!nickname.value || !password.value) {
    alert('닉네임과 비밀번호를 입력해주세요.')
    return
  }
  
  const success = await authStore.login(nickname.value, password.value)
  if (success) {
    // 로그인 성공 시 홈으로 이동
    router.push('/')
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">로그인</h1>
      
      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="input-group">
          <label>닉네임</label>
          <input 
            v-model="nickname" 
            type="text" 
            placeholder="닉네임을 입력하세요" 
            autofocus
          />
        </div>
        
        <div class="input-group">
          <label>비밀번호</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="비밀번호를 입력하세요" 
          />
        </div>

        <p v-if="authStore.error" class="error-msg">
          {{ authStore.error }}
        </p>

        <button 
          type="submit" 
          class="submit-btn" 
          :disabled="authStore.loading"
        >
          {{ authStore.loading ? '로그인 중...' : '로그인' }}
        </button>
      </form>

      <div class="auth-footer">
        계정이 없으신가요? 
        <RouterLink :to="{ name: 'signup' }" class="link-text">
          회원가입
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* (스타일은 아래 회원가입 페이지와 공통으로 사용하셔도 됩니다) */
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px); /* 헤더 높이 제외 대략 */
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: #141414;
  border: 1px solid #1f2937;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.5);
}

.auth-title {
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: #f5f5f7;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 6px;
}

.input-group input {
  width: 100%;
  background: #0a0a0a;
  border: 1px solid #2d3748;
  border-radius: 8px;
  padding: 12px;
  color: white;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}

.input-group input:focus {
  border-color: #3b82f6;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #1d4ed8;
}

.submit-btn:disabled {
  background: #4b5563;
  cursor: not-allowed;
}

.error-msg {
  color: #ef4444;
  font-size: 13px;
  margin-bottom: 12px;
  text-align: center;
}

.auth-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #9ca3af;
}

.link-text {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 600;
  margin-left: 4px;
}
</style>