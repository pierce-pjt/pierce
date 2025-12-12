<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const nickname = ref('')
const password = ref('')
const confirmPassword = ref('')

const handleSignup = async () => {
  if (!nickname.value || !password.value) {
    alert('모든 항목을 입력해주세요.')
    return
  }
  if (password.value !== confirmPassword.value) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }
  
  const success = await authStore.register(nickname.value, password.value)
  if (success) {
    alert('회원가입이 완료되었습니다! 로그인해주세요.')
    router.push('/login')
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="auth-title">회원가입</h1>
      
      <form @submit.prevent="handleSignup" class="auth-form">
        <div class="input-group">
          <label>닉네임</label>
          <input 
            v-model="nickname" 
            type="text" 
            placeholder="사용하실 닉네임" 
          />
        </div>
        
        <div class="input-group">
          <label>비밀번호</label>
          <input 
            v-model="password" 
            type="password" 
            placeholder="비밀번호" 
          />
        </div>

        <div class="input-group">
          <label>비밀번호 확인</label>
          <input 
            v-model="confirmPassword" 
            type="password" 
            placeholder="비밀번호 확인" 
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
          {{ authStore.loading ? '가입 중...' : '회원가입' }}
        </button>
      </form>

      <div class="auth-footer">
        이미 계정이 있으신가요? 
        <RouterLink :to="{ name: 'login' }" class="link-text">
          로그인
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* LoginView.vue와 동일한 스타일을 사용하거나, global css로 빼서 사용 */
/* 편의상 LoginView와 동일한 CSS를 그대로 붙여넣어 주세요 */
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 200px);
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
.input-group { margin-bottom: 20px; }
.input-group label { display: block; font-size: 13px; color: #9ca3af; margin-bottom: 6px; }
.input-group input {
  width: 100%; background: #0a0a0a; border: 1px solid #2d3748;
  border-radius: 8px; padding: 12px; color: white; font-size: 15px; outline: none;
}
.input-group input:focus { border-color: #3b82f6; }
.submit-btn {
  width: 100%; padding: 12px; background: #2563eb; color: white; border: none;
  border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 8px;
}
.submit-btn:hover { background: #1d4ed8; }
.submit-btn:disabled { background: #4b5563; }
.error-msg { color: #ef4444; font-size: 13px; margin-bottom: 12px; text-align: center; }
.auth-footer { margin-top: 20px; text-align: center; font-size: 14px; color: #9ca3af; }
.link-text { color: #3b82f6; text-decoration: none; font-weight: 600; margin-left: 4px; }
</style>