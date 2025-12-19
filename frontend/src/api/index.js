// src/api/index.js
import axios from 'axios'

// axios 기본 설정
axios.defaults.baseURL = '/api'  // Django 백엔드 API 경로
axios.defaults.withCredentials = true  // 세션 쿠키 전송 허용
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

// 요청 인터셉터 (필요시)
axios.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터 (에러 처리)
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 로그인 필요
      console.warn('로그인이 필요합니다.')
      // router.push('/login')  // 필요시 활성화
    }
    return Promise.reject(error)
  }
)

export default axios