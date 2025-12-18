<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth' // ✅ Auth 스토어 추가

const router = useRouter()
const authStore = useAuthStore()

const stocks = ref([])
const loading = ref(false)
const watchlist = ref([]) // ✅ 관심종목 리스트 상태 추가

// API 호출 경로
const API_BASE = '/api'

// 종목 리스트 (확장 가능)
const TICKERS = [
  { code: '005930', name: '삼성전자' },
  { code: '000660', name: 'SK하이닉스' },
  { code: '373220', name: 'LG에너지솔루션' },
  { code: '035720', name: '카카오' },
  { code: '035420', name: 'NAVER' },
  { code: '005380', name: '현대차' },
  { code: '000270', name: '기아' },
]

// 상세 페이지 이동
const goStockDetail = (stock) => {
  router.push({ name: 'stock-detail', params: { code: stock.code } })
}

// 미니 차트용 포인트 계산
const getChartPoints = (data) => {
  if (!data || data.length < 2) return ''
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  return data.map((v, i) => {
    const x = (i / (data.length - 1)) * 80
    const y = 40 - ((v - min) / range) * 40
    return `${x},${y}`
  }).join(' ')
}

// ✅ 관심종목 가져오기
const fetchWatchlist = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const res = await fetch(`${API_BASE}/watchlist/`)
    if (res.ok) {
      const data = await res.json()
      // data는 [{ticker: '005930', ...}, ...] 형태
      watchlist.value = data.map(item => item.ticker)
    }
  } catch (e) {
    console.error(e)
  }
}

// ✅ 관심종목 토글 (별 클릭)
const toggleWatchlist = async (ticker) => {
  if (!authStore.isAuthenticated) {
    alert('로그인이 필요한 서비스입니다.')
    return
  }
  
  try {
    const res = await fetch(`${API_BASE}/watchlist/toggle/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker })
    })
    
    if (res.ok) {
      const data = await res.json()
      if (data.added) {
        watchlist.value.push(ticker)
      } else {
        watchlist.value = watchlist.value.filter(t => t !== ticker)
      }
    }
  } catch (e) {
    console.error(e)
  }
}

// 데이터 불러오기
const fetchStocks = async () => {
  loading.value = true
  const results = []
  try {
    for (const item of TICKERS) {
      // 1. 요약 정보
      const sumRes = await fetch(`${API_BASE}/stock-prices/summary/?ticker=${item.code}`)
      if (!sumRes.ok) continue
      const summary = await sumRes.json()

      // 2. 미니 차트 (7일)
      const chartRes = await fetch(`${API_BASE}/stock-prices/chart/?ticker=${item.code}&days=7`)
      let chartData = []
      if (chartRes.ok) {
        const chartJson = await chartRes.json()
        chartData = chartJson.map(row => Number(row.close))
      }

      results.push({
        ...summary, 
        chartData,
        displayName: item.name 
      })
    }
    // 거래량 순 정렬
    results.sort((a, b) => Number(b.volume) - Number(a.volume))
    stocks.value = results.map((s, idx) => ({ ...s, rank: idx + 1 }))
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStocks()
  fetchWatchlist() // ✅ 마운트 시 관심종목 목록 불러오기
})
</script>

<template>
  <div class="home-page">
    <section class="market-grid">
      <div class="market-card">
        <div class="market-label">코스피</div>
        <div class="market-value">2,645.57 <span class="up">▲ 1.2%</span></div>
      </div>
      <div class="market-card">
        <div class="market-label">코스닥</div>
        <div class="market-value">878.45 <span class="up">▲ 0.8%</span></div>
      </div>
      <div class="market-card">
        <div class="market-label">환율 (USD)</div>
        <div class="market-value">1,324.50 <span class="down">▼ 0.3%</span></div>
      </div>
    </section>

    <section class="stocks-card">
      <h2>실시간 인기 종목</h2>
      <div class="table-wrapper">
        <table class="stocks-table">
          <thead>
            <tr>
              <th width="50">관심</th> <th>순위</th>
              <th>종목명</th>
              <th>현재가</th>
              <th>등락률</th>
              <th>차트</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="6" class="center">로딩 중...</td></tr>
            <tr 
              v-else 
              v-for="stock in stocks" 
              :key="stock.code" 
              @click="goStockDetail(stock)" 
              class="stock-row"
            >
              <td class="center" @click.stop="toggleWatchlist(stock.code)">
                <span :class="watchlist.includes(stock.code) ? 'star-filled' : 'star-empty'">★</span>
              </td>

              <td>{{ stock.rank }}</td>
              <td>
                <div class="name-col">
                  <span class="name">{{ stock.name || stock.displayName }}</span>
                  <span class="code">{{ stock.code }}</span>
                </div>
              </td>
              <td class="right">{{ Number(stock.last_price).toLocaleString() }}</td>
              <td class="right" :class="stock.change_rate >= 0 ? 'red' : 'blue'">
                {{ stock.change_rate > 0 ? '+' : '' }}{{ stock.change_rate }}%
              </td>
              <td class="center">
                <svg width="80" height="40">
                  <polyline 
                    :points="getChartPoints(stock.chartData)" 
                    fill="none" 
                    :stroke="stock.change_rate >= 0 ? '#ef4444' : '#3b82f6'" 
                    stroke-width="2" 
                  />
                </svg>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page { max-width: 1120px; margin: 0 auto; color: #f5f5f7; }
.market-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.market-card { background: #141414; padding: 20px; border-radius: 16px; border: 1px solid #1f2937; }
.market-label { color: #9ca3af; font-size: 13px; margin-bottom: 8px; }
.market-value { font-size: 20px; font-weight: 600; }
.up { color: #ef4444; font-size: 14px; margin-left: 8px; }
.down { color: #3b82f6; font-size: 14px; margin-left: 8px; }

.stocks-card { background: #141414; border-radius: 16px; border: 1px solid #1f2937; overflow: hidden; }
.stocks-card h2 { padding: 20px; margin: 0; border-bottom: 1px solid #1f2937; font-size: 18px; }
.stocks-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.stocks-table th { text-align: left; color: #9ca3af; padding: 12px 20px; background: #0a0a0a; }
.stocks-table td { padding: 12px 20px; border-top: 1px solid #1f2937; }
.stock-row:hover { background: #1a1a1a; cursor: pointer; }

.name-col { display: flex; flex-direction: column; }
.name { font-weight: 600; }
.code { font-size: 11px; color: #6b7280; }
.right { text-align: right; }
.center { text-align: center; }
.red { color: #ef4444; }
.blue { color: #3b82f6; }

/* ✅ 별 아이콘 스타일 */
.star-filled { color: gold; cursor: pointer; font-size: 20px; }
.star-empty { color: #444; cursor: pointer; font-size: 20px; }
.star-empty:hover { color: #888; }
</style>