// src/api/mypage.js
import axios from './index'

export const mypageAPI = {
  getMyInfo: () => axios.get('/users/me/'),
  getPortfolioSummary: () => axios.get('/users/me/portfolio-summary/'),
  getHoldings: () => axios.get('/users/me/holdings/'),
  getTransactions: (limit = null) => {
    const params = limit ? { limit } : {}
    return axios.get('/users/me/transactions/', { params })
  },
  
  // 👇 watchlist-items → watchlist 로 변경
  getWatchlist: () => axios.get('/watchlist/'),
  toggleWatchlist: (ticker) => axios.post('/watchlist/toggle/', { ticker }),
  
  // 전략 메모는 그대로 (이미 일치함)
  getStrategyNotes: () => axios.get('/strategy-notes/'),
  createStrategyNote: (data) => axios.post('/strategy-notes/', data),
  updateStrategyNote: (id, data) => axios.put(`/strategy-notes/${id}/`, data),
  deleteStrategyNote: (id) => axios.delete(`/strategy-notes/${id}/`),
  
  // 회원정보 수정
  updateProfile: (userId, data) => axios.patch(`/users/${userId}/`, data),
  
  // 작성글 
  getMyPosts: () => axios.get('/users/me/posts/'),
  getLikedPosts: () => axios.get('/users/me/liked-posts/'),
}