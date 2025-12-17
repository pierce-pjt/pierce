<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth' // ✅ Auth 스토어 추가

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore() // ✅
const code = route.params.code

const summary = ref(null)
const chartData = ref([])
const posts = ref([])
const loading = ref(true)

// 💰 모의투자 관련 상태
const showTradeModal = ref(false)
const tradeType = ref('BUY')
const tradeQuantity = ref(0)

// 차트 SVG 패스 생성
const chartPath = computed(() => {
  if (!chartData.value.length) return ''
  const data = chartData.value
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  return data.map((v, i) => {
    const x = (i / (data.length - 1)) * 800
    const y = 300 - ((v - min) / range) * 300
    return `${x},${y}`
  }).join(' ')
})

const fetchData = async () => {
  loading.value = true
  try {
    // 1. 요약
    const sumRes = await fetch(`/api/stock-prices/summary/?ticker=${code}`)
    if (sumRes.ok) summary.value = await sumRes.json()

    // 2. 30일 차트
    const chartRes = await fetch(`/api/stock-prices/chart/?ticker=${code}&days=30`)
    if (chartRes.ok) {
      const json = await chartRes.json()
      chartData.value = json.map(row => Number(row.close))
    }

    // 3. 종목 토론글
    const feedRes = await fetch(`/api/posts/feed/?ticker=${code}`)
    if (feedRes.ok) posts.value = await feedRes.json()

  } catch(e) { console.error(e) } 
  finally { loading.value = false }
}

// 💰 거래 모달 열기
const openTradeModal = (type) => {
  if(!authStore.isAuthenticated) return alert('로그인이 필요한 기능입니다.')
  tradeType.value = type
  tradeQuantity.value = 0 // 초기화
  showTradeModal.value = true
}

// 💰 거래 실행
const executeTrade = async () => {
  if (tradeQuantity.value <= 0) return alert('수량을 올바르게 입력해주세요.')
  
  const price = summary.value.last_price
  const amount = price * tradeQuantity.value

  // 매수 시 마일리지 체크
  if (tradeType.value === 'BUY' && authStore.user.mileage < amount) {
    return alert(`마일리지가 부족합니다! (부족액: ${(amount - authStore.user.mileage).toLocaleString()} M)`)
  }

  try {
    const res = await fetch('/api/transactions/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        company: code, 
        type: tradeType.value,
        price: price,
        quantity: tradeQuantity.value
      })
    })

    if(res.ok) {
      alert(`${tradeType.value === 'BUY' ? '매수' : '매도'} 주문이 체결되었습니다!`)
      await authStore.fetchUser() // 마일리지 갱신
      showTradeModal.value = false
    } else {
      const err = await res.json()
      alert(err.detail || '거래 실패')
    }
  } catch (e) {
    console.error(e)
    alert('서버 오류가 발생했습니다.')
  }
}

onMounted(() => fetchData())
</script>

<template>
  <div class="detail-page">
    <div v-if="loading" class="loading">로딩 중...</div>
    <div v-else class="content">
      
      <div class="header">
        <button @click="router.back()" class="back-btn">←</button>
        <div class="header-info">
          <h1 class="title">{{ summary?.name }} <span class="code">{{ code }}</span></h1>
          <div class="price-row">
            <div class="price" :class="summary?.change_rate >= 0 ? 'red' : 'blue'">
              {{ Number(summary?.last_price).toLocaleString() }}원
              <span class="change">{{ summary?.change_rate }}%</span>
            </div>
            
            <div class="trading-actions">
               <div v-if="authStore.isAuthenticated" class="my-mileage">
                 💎 {{ Number(authStore.user?.mileage || 0).toLocaleString() }} M
               </div>
               <button class="trade-btn buy" @click="openTradeModal('BUY')">매수</button>
               <button class="trade-btn sell" @click="openTradeModal('SELL')">매도</button>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-box">
        <svg viewBox="0 0 800 300" class="chart-svg">
          <polyline 
            :points="chartPath" 
            fill="none" 
            :stroke="summary?.change_rate >= 0 ? '#ef4444' : '#3b82f6'" 
            stroke-width="2" 
          />
        </svg>
      </div>

      <div class="feed-section">
        <h3>종목 토론방 ({{ posts.length }})</h3>
        <div v-if="posts.length === 0" class="empty">게시글이 없습니다.</div>
        <div v-else class="feed-list">
          <div v-for="post in posts" :key="post.id" class="feed-item">
            <div class="feed-head">
              <span class="author">{{ post.author.nickname || '익명' }}</span>
              <span class="date">{{ new Date(post.created_at).toLocaleDateString() }}</span>
            </div>
            <div class="feed-body">{{ post.content }}</div>
            <div v-if="post.image_url" class="feed-img-wrapper">
              <img :src="post.image_url" class="feed-img" />
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-if="showTradeModal" class="modal-overlay" @click.self="showTradeModal = false">
      <div class="modal-content trade-modal">
        <h3>{{ tradeType === 'BUY' ? '매수' : '매도' }} 주문</h3>
        <div class="trade-info">
          <p>종목: <strong>{{ summary?.name }}</strong></p>
          <p>현재가: <strong>{{ Number(summary?.last_price).toLocaleString() }}원</strong></p>
        </div>
        
        <div class="input-group">
          <label>수량</label>
          <input type="number" v-model.number="tradeQuantity" class="trade-input" min="1" />
        </div>
        
        <div class="total-amount">
          총 주문금액: <span>{{ Number(summary?.last_price * tradeQuantity).toLocaleString() }} M</span>
        </div>
        
        <div class="modal-actions">
          <button @click="showTradeModal = false" class="cancel-btn">취소</button>
          <button 
            @click="executeTrade" 
            class="submit-btn"
            :class="tradeType === 'BUY' ? 'buy-bg' : 'sell-bg'"
          >
            주문하기
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.detail-page { max-width: 800px; margin: 0 auto; color: #f5f5f7; padding-bottom: 60px; }

/* 헤더 & 가격 */
.header { display: flex; align-items: flex-start; gap: 20px; margin-bottom: 24px; }
.back-btn { background: #1f2937; border: none; color: white; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-size: 20px; flex-shrink: 0; }
.header-info { flex-grow: 1; }
.title { margin: 0; font-size: 24px; }
.code { font-size: 16px; color: #9ca3af; font-weight: normal; margin-left: 8px; }
.price-row { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 8px; flex-wrap: wrap; gap: 10px; }
.price { font-size: 28px; font-weight: 700; }
.change { font-size: 16px; margin-left: 10px; }
.red { color: #ef4444; } .blue { color: #3b82f6; }

/* 💰 트레이딩 버튼 스타일 */
.trading-actions { display: flex; align-items: center; gap: 10px; }
.my-mileage { font-size: 14px; color: #fbbf24; font-weight: bold; background: rgba(251, 191, 36, 0.1); padding: 6px 10px; border-radius: 8px; }
.trade-btn { padding: 8px 16px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; color: white; }
.trade-btn.buy { background: #ef4444; }
.trade-btn.sell { background: #3b82f6; }
.trade-btn:hover { opacity: 0.9; }

/* 차트 */
.chart-box { background: #141414; border: 1px solid #1f2937; border-radius: 16px; padding: 20px; margin-bottom: 30px; }
.chart-svg { width: 100%; height: auto; }

/* 피드 */
.feed-section h3 { border-bottom: 1px solid #1f2937; padding-bottom: 10px; margin-bottom: 16px; }
.feed-item { background: #141414; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 12px; }
.feed-head { display: flex; justify-content: space-between; color: #9ca3af; font-size: 13px; margin-bottom: 8px; }
.feed-img-wrapper { margin-top: 10px; border-radius: 8px; overflow: hidden; }
.feed-img { max-width: 100%; max-height: 300px; object-fit: cover; }
.empty { text-align: center; color: #6b7280; padding: 30px; }

/* 모달 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 100; backdrop-filter: blur(4px); }
.modal-content { background: #1f2937; padding: 24px; border-radius: 16px; width: 90%; max-width: 400px; color: #f5f5f7; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
.trade-info { background: #111827; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
.trade-info p { margin: 4px 0; display: flex; justify-content: space-between; }
.input-group { margin-bottom: 20px; }
.input-group label { display: block; margin-bottom: 6px; font-size: 14px; color: #9ca3af; }
.trade-input { width: 100%; background: #374151; border: 1px solid #4b5563; color: white; padding: 10px; border-radius: 8px; font-size: 16px; box-sizing: border-box; }
.total-amount { text-align: right; margin-bottom: 24px; font-size: 18px; font-weight: bold; }
.total-amount span { color: #fbbf24; }
.modal-actions { display: flex; gap: 10px; }
.cancel-btn { flex: 1; background: #374151; color: white; border: none; padding: 12px; border-radius: 8px; cursor: pointer; }
.submit-btn { flex: 2; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; }
.buy-bg { background: #ef4444; }
.sell-bg { background: #3b82f6; }
</style>