// src/stores/auth.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isAuthenticated = ref(false)
  const loading = ref(false)
  const error = ref(null)
  const router = useRouter()
  
  // API 프록시 설정이 되어있다고 가정 (/api -> http://localhost:8000/api)
  const API_BASE = '/api'

  // 1. 로그인
  const login = async (nickname, password) => {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/users/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nickname, password }),
        // ❗ 세션 쿠키 교환을 위해 필수
        credentials: 'include' 
      })

      if (!res.ok) {
        // 백엔드 에러 메시지 처리 시도
        const data = await res.json().catch(() => ({}))
        throw new Error(data.message || '로그인에 실패했습니다.')
      }

      // 로그인 성공 시 내 정보 가져오기
      await fetchUser()
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  // 2. 회원가입
  const register = async (nickname, password) => {
    loading.value = true
    error.value = null
    try {
      // 프로필 이미지는 임시로 랜덤 아바타 서비스 사용
      const profile_image_url = `https://api.dicebear.com/7.x/adventurer/svg?seed=${nickname}`

      const res = await fetch(`${API_BASE}/users/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          nickname, 
          password,
          profile_image_url 
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.message || '회원가입에 실패했습니다.')
      }
      
      return true
    } catch (err) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  // 3. 내 정보 가져오기 (새로고침 시 로그인 유지용)
  const fetchUser = async () => {
    try {
      const res = await fetch(`${API_BASE}/users/me/`, {
        method: 'GET',
        credentials: 'include'
      })
      
      if (res.ok) {
        const userData = await res.json()
        user.value = userData
        isAuthenticated.value = true
      } else {
        // 세션 만료 혹은 비로그인
        user.value = null
        isAuthenticated.value = false
      }
    } catch (err) {
      console.error(err)
      user.value = null
      isAuthenticated.value = false
    }
  }

  // 4. 로그아웃
  const logout = async () => {
    try {
      await fetch(`${API_BASE}/users/logout/`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error(err)
    } finally {
      user.value = null
      isAuthenticated.value = false
      // 홈으로 리다이렉트
      if (router) router.push('/')
      else window.location.href = '/'
    }
  }

  return { 
    user, 
    isAuthenticated, 
    loading, 
    error, 
    login, 
    register, 
    fetchUser, 
    logout 
  }
})