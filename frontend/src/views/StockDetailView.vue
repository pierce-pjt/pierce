<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { mypageAPI } from '@/api/mypage' 
import VueApexCharts from 'vue3-apexcharts'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const code = route.params.code 

// --- 상태 관리 ---
const summary = ref(null)
const posts = ref([])
const loading = ref(true)
const activeTab = ref('chart') 
const tradeLogs = ref([])      
const watchlist = ref([])

// 📈 차트 데이터 상태
const fullChartData = ref([]) 
const fullMAData = ref([]) // 🆕 전체 MA 데이터 저장
const fullBollingerData = ref([]) // 🆕 전체 볼린저 데이터 저장
const chartSeries = ref([])   
const activeRange = ref('1M')
const activeIndicator = ref('none')
const volumeSeries = ref([])
const maSeries = ref([])
const bollingerSeries = ref([])

// 🆕 로딩 상태
const indicatorLoading = ref(false)

// --- Computed ---
const isWatched = computed(() => watchlist.value.includes(code))

const priceColorClass = computed(() => {
  const rate = summary.value?.change_rate || 0
  if (rate > 0) return 'text-red'
  if (rate < 0) return 'text-blue'
  return 'text-gray'
})

const isHighVolatility = computed(() => Math.abs(summary.value?.change_rate || 0) >= 5.0)

const getTickAmount = () => {
  if (!fullChartData.value.length) return 10

  const firstDate = dayjs(fullChartData.value[0].date)
  const lastDate = dayjs(fullChartData.value[fullChartData.value.length - 1].date)
  const daysDiff = lastDate.diff(firstDate, 'day')

  if (daysDiff <= 7) return 7
  else if (daysDiff <= 30) return 10
  else if (daysDiff <= 90) return 12
  else if (daysDiff <= 365) return 12
  else return 10
}

// ✅ 메인 차트 옵션
const chartOptions = computed(() => ({
  chart: {
    type: 'candlestick',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, speed: 600 }
  },
  theme: { mode: 'dark' },
  xaxis: { 
    type: 'category', 
    labels: { 
      style: { colors: '#777', fontSize: '11px' },
      formatter: (val) => val,
      rotate: -45,
      rotateAlways: false,
      hideOverlappingLabels: true,
      trim: true,
      maxHeight: 120
    },
    tickAmount: getTickAmount(),
    tickPlacement: 'on',
    axisBorder: { show: false },
    tooltip: { enabled: false }
  },
  yaxis: {
    opposite: true,
    labels: { 
      style: { colors: '#777' },
      formatter: (val) => val?.toLocaleString() 
    }
  },
  grid: { 
    borderColor: '#222', 
    strokeDashArray: 4, 
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } }
  },
  plotOptions: {
    candlestick: { 
      colors: { upward: '#f04452', downward: '#3182f6' },
      wick: { useFillColor: true }
    }
  },
  tooltip: {
    theme: 'dark',
    x: { 
      format: 'yyyy-MM-dd'
    },
    y: {
      formatter: (val) => val?.toLocaleString() + '원'
    }
  }
}))

// 이동평균선 차트 옵션
const maChartOptions = computed(() => ({
  ...chartOptions.value,
  stroke: {
    width: [1, 2, 2, 2],
    dashArray: [0, 0, 0, 0]
  },
  colors: ['#f04452', '#fbbf24', '#10b981', '#3182f6'],
  legend: {
    show: true,
    position: 'top',
    horizontalAlign: 'left',
    labels: { colors: '#999' }
  }
}))

// 거래량 차트 옵션
const volumeChartOptions = computed(() => ({
  chart: {
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false },
    height: 120
  },
  theme: { mode: 'dark' },
  xaxis: {
    type: 'category',
    labels: { show: false },
    axisBorder: { show: false }
  },
  yaxis: {
    opposite: true,
    labels: {
      style: { colors: '#777', fontSize: '10px' },
      formatter: (val) => (val / 1000).toFixed(0) + 'K'
    }
  },
  plotOptions: {
    bar: {
      colors: {
        ranges: [{
          from: 0,
          to: Infinity,
          color: '#f04452'
        }]
      }
    }
  },
  grid: { 
    borderColor: '#222', 
    strokeDashArray: 4,
    yaxis: { lines: { show: true } }
  },
  dataLabels: { enabled: false },
  tooltip: {
    theme: 'dark',
    y: { formatter: (val) => val?.toLocaleString() }
  }
}))

// 볼린저 밴드 차트 옵션
const bollingerChartOptions = computed(() => ({
  ...chartOptions.value,
  stroke: {
    width: [1, 2, 2, 2],
    dashArray: [0, 5, 0, 5]
  },
  colors: ['#f04452', '#999', '#3182f6', '#999'],
  legend: {
    show: true,
    position: 'top',
    horizontalAlign: 'left',
    labels: { colors: '#999' }
  }
}))

// 🆕 필터링 헬퍼
const filterDataByRange = (data, range) => {
  if (!data || !data.length) return []
  
  const lastDataDate = dayjs(data[data.length - 1].date)
  let startDate
  if (range === '1W') startDate = lastDataDate.subtract(7, 'day')
  else if (range === '1M') startDate = lastDataDate.subtract(1, 'month')
  else if (range === '1Y') startDate = lastDataDate.subtract(1, 'year')
  
  return data.filter(d => dayjs(d.date).isAfter(startDate) || dayjs(d.date).isSame(startDate))
}

// 🆕 거래량 계산
const calculateVolume = (data) => {
  volumeSeries.value = [{
    name: '거래량',
    data: data.map(d => ({ x: dayjs(d.date).format('MM/DD'), y: d.volume || 0 }))
  }]
}

// 🆕 이동평균선 데이터 가져오기
const fetchMA = async () => {
  indicatorLoading.value = true
  try {
    const res = await fetch(`/api/stock-prices/moving-averages/?ticker=${code}&days=365`, { 
      credentials: 'include' 
    })
    
    if (!res.ok) throw new Error('MA fetch failed')
    
    const data = await res.json()
    console.log('MA data received:', data.length, 'items') // 🔍 디버깅
    
    fullMAData.value = data // 전체 데이터 저장
    
    // 기간 필터링
    const filtered = filterDataByRange(data, activeRange.value)
    console.log('Filtered MA data:', filtered.length, 'items') // 🔍 디버깅
    
    if (filtered.length === 0) {
      console.error('No data after filtering!')
      return
    }
    
    maSeries.value = [
      { 
        name: '가격', 
        type: 'candlestick',
        data: filtered.map(d => ({
          x: dayjs(d.date).format('MM/DD'),
          y: [d.open, d.high, d.low, d.close]
        }))
      },
      { 
        name: 'MA(5)', 
        type: 'line',
        data: filtered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.ma5 
        })).filter(d => d.y !== null)
      },
      { 
        name: 'MA(20)', 
        type: 'line',
        data: filtered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.ma20 
        })).filter(d => d.y !== null)
      },
      { 
        name: 'MA(60)', 
        type: 'line',
        data: filtered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.ma60 
        })).filter(d => d.y !== null)
      }
    ]
    
    console.log('MA series:', maSeries.value) // 🔍 디버깅
  } catch (e) {
    console.error("이동평균선 로드 실패:", e)
  } finally {
    indicatorLoading.value = false
  }
}

// 🆕 볼린저 밴드 데이터 가져오기
const fetchBollinger = async () => {
  indicatorLoading.value = true
  try {
    const res = await fetch(`/api/stock-prices/bollinger-bands/?ticker=${code}&days=365`, { 
      credentials: 'include' 
    })
    
    if (!res.ok) throw new Error('Bollinger fetch failed')
    
    const data = await res.json()
    console.log('Bollinger data received:', data.length, 'items') // 🔍 디버깅
    
    fullBollingerData.value = data // 전체 데이터 저장
    
    // 기간 필터링
    const filtered = filterDataByRange(data, activeRange.value)
    console.log('Filtered Bollinger data:', filtered.length, 'items') // 🔍 디버깅
    
    if (filtered.length === 0) {
      console.error('No data after filtering!')
      return
    }
    
    bollingerSeries.value = [
      { 
        name: '가격', 
        type: 'candlestick',
        data: filtered.map(d => ({
          x: dayjs(d.date).format('MM/DD'),
          y: [d.open, d.high, d.low, d.close]
        }))
      },
      { 
        name: '상단 밴드', 
        type: 'line',
        data: filtered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.upper_band 
        })).filter(d => d.y !== null)
      },
      { 
        name: '중심선 (SMA)', 
        type: 'line',
        data: filtered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.sma 
        })).filter(d => d.y !== null)
      },
      { 
        name: '하단 밴드', 
        type: 'line',
        data: filtered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.lower_band 
        })).filter(d => d.y !== null)
      }
    ]
    
    console.log('Bollinger series:', bollingerSeries.value) // 🔍 디버깅
  } catch (e) {
    console.error("볼린저 밴드 로드 실패:", e)
  } finally {
    indicatorLoading.value = false
  }
}

// 🆕 지표 변경 감지
watch(activeIndicator, (newIndicator) => {
  if (newIndicator === 'ma') {
    if (fullMAData.value.length > 0) {
      // 이미 데이터가 있으면 필터링만
      const filtered = filterDataByRange(fullMAData.value, activeRange.value)
      maSeries.value = [
        { 
          name: '가격', 
          type: 'candlestick',
          data: filtered.map(d => ({
            x: dayjs(d.date).format('MM/DD'),
            y: [d.open, d.high, d.low, d.close]
          }))
        },
        { 
          name: 'MA(5)', 
          type: 'line',
          data: filtered.map(d => ({ 
            x: dayjs(d.date).format('MM/DD'), 
            y: d.ma5 
          })).filter(d => d.y !== null)
        },
        { 
          name: 'MA(20)', 
          type: 'line',
          data: filtered.map(d => ({ 
            x: dayjs(d.date).format('MM/DD'), 
            y: d.ma20 
          })).filter(d => d.y !== null)
        },
        { 
          name: 'MA(60)', 
          type: 'line',
          data: filtered.map(d => ({ 
            x: dayjs(d.date).format('MM/DD'), 
            y: d.ma60 
          })).filter(d => d.y !== null)
        }
      ]
    } else {
      fetchMA()
    }
  } else if (newIndicator === 'bollinger') {
    if (fullBollingerData.value.length > 0) {
      // 이미 데이터가 있으면 필터링만
      const filtered = filterDataByRange(fullBollingerData.value, activeRange.value)
      bollingerSeries.value = [
        { 
          name: '가격', 
          type: 'candlestick',
          data: filtered.map(d => ({
            x: dayjs(d.date).format('MM/DD'),
            y: [d.open, d.high, d.low, d.close]
          }))
        },
        { 
          name: '상단 밴드', 
          type: 'line',
          data: filtered.map(d => ({ 
            x: dayjs(d.date).format('MM/DD'), 
            y: d.upper_band 
          })).filter(d => d.y !== null)
        },
        { 
          name: '중심선 (SMA)', 
          type: 'line',
          data: filtered.map(d => ({ 
            x: dayjs(d.date).format('MM/DD'), 
            y: d.sma 
          })).filter(d => d.y !== null)
        },
        { 
          name: '하단 밴드', 
          type: 'line',
          data: filtered.map(d => ({ 
            x: dayjs(d.date).format('MM/DD'), 
            y: d.lower_band 
          })).filter(d => d.y !== null)
        }
      ]
    } else {
      fetchBollinger()
    }
  }
})

// --- 데이터 로직 ---
const fetchWatchlist = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const res = await fetch('/api/watchlist/', { credentials: 'include' })
    if (res.ok) {
      const data = await res.json()
      const items = data.results || data 
      if (Array.isArray(items)) watchlist.value = items.map(item => item.ticker)
    }
  } catch (e) { console.error("관심종목 로드 실패", e) }
}

const toggleWatchlist = async () => {
  if (!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  try {
    const res = await fetch('/api/watchlist/toggle/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ ticker: code })
    })
    if (res.ok) {
      const result = await res.json()
      if (result.added) { 
        if (!watchlist.value.includes(code)) watchlist.value.push(code) 
      } else { 
        watchlist.value = watchlist.value.filter(c => c !== code) 
      }
    }
  } catch (e) { console.error("관심종목 토글 실패", e) }
}

// 기간 변경
const updateChartRange = async (range) => {
  activeRange.value = range
  if (!fullChartData.value.length) return
  
  // 기본 차트 데이터 필터링
  const filtered = filterDataByRange(fullChartData.value, range)
  
  chartSeries.value = [{
    name: '주가',
    data: filtered.map(d => ({
      x: dayjs(d.date).format('MM/DD'),
      y: [d.open, d.high, d.low, d.close]
    }))
  }]
  
  // 거래량 계산
  calculateVolume(filtered)
  
  // 🆕 현재 활성화된 지표가 있으면 다시 필터링
  if (activeIndicator.value === 'ma' && fullMAData.value.length > 0) {
    const maFiltered = filterDataByRange(fullMAData.value, range)
    maSeries.value = [
      { 
        name: '가격', 
        type: 'candlestick',
        data: maFiltered.map(d => ({
          x: dayjs(d.date).format('MM/DD'),
          y: [d.open, d.high, d.low, d.close]
        }))
      },
      { 
        name: 'MA(5)', 
        type: 'line',
        data: maFiltered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.ma5 
        })).filter(d => d.y !== null)
      },
      { 
        name: 'MA(20)', 
        type: 'line',
        data: maFiltered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.ma20 
        })).filter(d => d.y !== null)
      },
      { 
        name: 'MA(60)', 
        type: 'line',
        data: maFiltered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.ma60 
        })).filter(d => d.y !== null)
      }
    ]
  } else if (activeIndicator.value === 'bollinger' && fullBollingerData.value.length > 0) {
    const bollingerFiltered = filterDataByRange(fullBollingerData.value, range)
    bollingerSeries.value = [
      { 
        name: '가격', 
        type: 'candlestick',
        data: bollingerFiltered.map(d => ({
          x: dayjs(d.date).format('MM/DD'),
          y: [d.open, d.high, d.low, d.close]
        }))
      },
      { 
        name: '상단 밴드', 
        type: 'line',
        data: bollingerFiltered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.upper_band 
        })).filter(d => d.y !== null)
      },
      { 
        name: '중심선 (SMA)', 
        type: 'line',
        data: bollingerFiltered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.sma 
        })).filter(d => d.y !== null)
      },
      { 
        name: '하단 밴드', 
        type: 'line',
        data: bollingerFiltered.map(d => ({ 
          x: dayjs(d.date).format('MM/DD'), 
          y: d.lower_band 
        })).filter(d => d.y !== null)
      }
    ]
  }
}

const fetchMyTransactions = async () => {
  if (!authStore.isAuthenticated) return
  try {
    const res = await mypageAPI.getTransactions()
    const allTrades = Array.isArray(res.data) ? res.data : []
    tradeLogs.value = allTrades
      .filter(tx => tx.ticker === code || tx.company_code === code)
      .sort((a, b) => new Date(b.transaction_datetime) - new Date(a.transaction_datetime))
      .slice(0, 15)
  } catch (e) { console.error("거래 내역 로드 실패:", e) }
}

const fetchData = async () => {
  try {
    const opt = { credentials: 'include' }
    const [sumRes, feedRes] = await Promise.all([
      fetch(`/api/stock-prices/summary/?ticker=${code}`, opt),
      fetch(`/api/posts/feed/?ticker=${code}`, opt)
    ])
    if (sumRes.ok) summary.value = await sumRes.json()
    if (feedRes.ok) posts.value = await feedRes.json()

    const chartRes = await fetch(`/api/stock-prices/chart/?ticker=${code}&days=365`, opt)
    if (chartRes.ok) {
      const json = await chartRes.json()
      const data = Array.isArray(json) ? json : (json.results || [])
      if (data.length > 0) {
        fullChartData.value = data
        updateChartRange(activeRange.value)
      }
    }
    await fetchMyTransactions()
  } catch(e) { console.error("데이터 로드 에러:", e) }
  finally { loading.value = false }
}

const goToPostDetail = (postId) => {
  router.push(`/community/${postId}`)
}

// --- 거래 로직 ---
const showTradeModal = ref(false)
const tradeType = ref('BUY')
const tradeQuantity = ref(0)

const openTradeModal = (type) => {
  if(!authStore.isAuthenticated) return alert('로그인이 필요합니다.')
  tradeType.value = type
  tradeQuantity.value = 0
  showTradeModal.value = true
}

const executeTrade = async () => {
  if (tradeQuantity.value <= 0) return alert('수량을 입력해주세요.')
  try {
    const res = await fetch('/api/transactions/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', 
      body: JSON.stringify({ 
        company: code, type: tradeType.value, 
        price: summary.value.last_price, quantity: tradeQuantity.value 
      })
    })
    if (res.ok) {
      alert(`${tradeType.value === 'BUY' ? '매수' : '매도'} 주문 체결!`)
      await authStore.fetchUser() 
      showTradeModal.value = false
      await fetchData() 
    } else {
      const errorData = await res.json()
      alert(errorData.detail || '거래 처리 오류')
    }
  } catch (e) { alert('통신 오류가 발생했습니다.') }
}

const formatPrice = (v) => v?.toLocaleString() || '0'
const formatDate = (d) => dayjs(d).format('MM.DD HH:mm')

let polling = null
watch(() => authStore.isAuthenticated, (newVal) => { if (newVal) fetchWatchlist() }, { immediate: true })

onMounted(() => { 
  fetchData()
  polling = setInterval(fetchData, 10000) 
})
onUnmounted(() => { if (polling) clearInterval(polling) })
</script>

<!-- 템플릿과 스타일은 동일 -->
<template>
  <div class="dashboard-detail">
    <header class="detail-header-hero">
      <div 
        class="hero-bg" 
        :style="{ backgroundImage: summary?.image_url ? `url(${summary.image_url})` : 'none' }"
      ></div>
      <div class="hero-gradient"></div>
      
      <div class="hero-content">
        <div class="hero-top-nav">
          <button @click="router.back()" class="back-btn">〈 뒤로가기</button>
        </div>
        
        <div class="hero-main-info">
          <div class="title-area">
            <div class="name-row">
              <h1 class="stock-title">{{ summary?.name || '로딩 중...' }}</h1>
              <button class="star-btn" @click="toggleWatchlist">
                {{ isWatched ? '★' : '☆' }}
              </button>
              <div v-if="isHighVolatility" class="warning-badge">투자경고</div>
            </div>
            <div class="price-info" :class="priceColorClass">
              <span class="main-price">{{ formatPrice(summary?.last_price) }}원</span>
              <span class="main-rate">
                {{ (summary?.change_rate || 0) > 0 ? '+' : '' }}{{ summary?.change_rate }}%
              </span>
            </div>
          </div>

          <div class="header-right" v-if="authStore.isAuthenticated">
            <div class="mileage-info">
              <span class="mileage-label">보유 자산</span>
              <div class="mileage-badge">💎 {{ formatPrice(authStore.user?.mileage) }} M</div>
            </div>
            <div class="action-btns">
              <button @click="openTradeModal('BUY')" class="btn buy-bg">BUY</button>
              <button @click="openTradeModal('SELL')" class="btn sell-bg">SELL</button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <nav class="toss-nav">
      <button @click="activeTab = 'chart'" :class="{ active: activeTab === 'chart' }">차트·호가</button>
      <button @click="activeTab = 'community'" :class="{ active: activeTab === 'community' }">커뮤니티</button>
    </nav>

    <div class="main-grid">
      <div class="content-left">
        <div v-if="activeTab === 'chart'">
          <section class="chart-section shadow-card">
            <div class="card-header">
              <div class="header-left">
                <h3 class="label-text">주가 흐름</h3>
                <div class="indicator-tabs-inline">
                  <button 
                    @click="activeIndicator = 'none'" 
                    :class="{ active: activeIndicator === 'none' }"
                    :disabled="indicatorLoading"
                  >
                    기본
                  </button>
                  <button 
                    @click="activeIndicator = 'ma'" 
                    :class="{ active: activeIndicator === 'ma' }"
                    :disabled="indicatorLoading"
                  >
                    이동평균선
                  </button>
                  <button 
                    @click="activeIndicator = 'bollinger'" 
                    :class="{ active: activeIndicator === 'bollinger' }"
                    :disabled="indicatorLoading"
                  >
                    볼린저 밴드
                  </button>
                </div>
              </div>
              <div class="range-tabs">
                <button 
                  v-for="r in ['1W', '1M', '1Y']" 
                  :key="r" 
                  @click="updateChartRange(r)" 
                  :class="{ active: activeRange === r }"
                >
                  {{ r }}
                </button>
              </div>
            </div>
            
              <div class="chart-wrapper">
                <div v-if="indicatorLoading" class="loading-state">
                  <v-progress-circular indeterminate color="primary"></v-progress-circular>
                  <p>데이터 계산 중...</p>
                </div>

                <template v-else>
                  <VueApexCharts 
                    v-if="activeIndicator === 'none' && chartSeries.length > 0"
                    key="chart-basic"
                    type="candlestick" 
                    height="400" 
                    :options="chartOptions" 
                    :series="chartSeries" 
                  />

                  <VueApexCharts 
                    v-else-if="activeIndicator === 'ma' && maSeries.length > 0"
                    key="chart-ma"
                    type="line"  height="400" 
                    :options="maChartOptions" 
                    :series="maSeries" 
                  />

                  <VueApexCharts 
                    v-else-if="activeIndicator === 'bollinger' && bollingerSeries.length > 0"
                    key="chart-bollinger"
                    type="line" 
                    height="400" 
                    :options="bollingerChartOptions" 
                    :series="bollingerSeries" 
                  />

                  <div v-else class="empty-state">차트 데이터를 불러올 수 없습니다.</div>
                </template>
              </div>

            <div class="volume-section">
              <div class="volume-header">
                <span class="volume-label">거래량</span>
              </div>
              <VueApexCharts 
                v-if="volumeSeries.length > 0"
                type="bar"
                height="120"
                :options="volumeChartOptions"
                :series="volumeSeries"
              />
            </div>
          </section>
        </div>

        <div v-if="activeTab === 'community'">
          <section class="feed-section shadow-card">
            <h3 class="label-text">종목 토론방</h3>
            <div v-if="posts.length === 0" class="empty-state">첫 게시글을 작성해보세요.</div>
            <div 
              v-for="post in posts" 
              :key="post.id" 
              class="post-item clickable"
              @click="goToPostDetail(post.id)"
            >
              <div class="post-meta">
                <span class="user">{{ post.author?.nickname || '익명' }}</span>
                <span class="time">{{ formatDate(post.created_at) }}</span>
              </div>
              <p class="post-text">{{ post.content }}</p>
              <span class="more-label">자세히 보기</span>
              
              <div class="post-stats">
                <span class="stat-item">❤️ {{ post.like_count || 0 }}</span>
                <span class="stat-item">💬 {{ post.comment_count || 0 }}</span>
              </div>
            </div>
          </section>
        </div>
      </div>

      <aside class="content-right">
        <section class="log-section shadow-card">
          <div class="log-header">
            <h3>나의 거래 내역</h3>
            <span v-if="authStore.isAuthenticated" class="live-dot"></span>
          </div>
          <div class="log-list custom-scrollbar">
            <div v-if="!authStore.isAuthenticated" class="empty-log">로그인 후 확인 가능합니다.</div>
            <div v-else-if="tradeLogs.length === 0" class="empty-log">거래 내역이 없습니다.</div>
            <div v-else v-for="log in tradeLogs" :key="log.id" class="log-item-v2">
              <div class="item-top">
                <span class="type-tag" :class="log.transaction_type === 'BUY' ? 'buy' : 'sell'">
                  {{ log.transaction_type === 'BUY' ? '매수' : '매도' }}
                </span>
                <span class="time">{{ formatDate(log.transaction_datetime) }}</span>
              </div>
              <div class="item-bottom">
                <span class="quantity">{{ log.quantity }}주 · {{ formatPrice(log.price) }}원</span>
                <span class="total-amount" :class="log.transaction_type === 'BUY' ? 'text-red' : 'text-blue'">
                  {{ log.transaction_type === 'BUY' ? '-' : '+' }}{{ formatPrice(log.amount) }}원
                </span>
              </div>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <div v-if="showTradeModal" class="modal-overlay" @click.self="showTradeModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h2 :class="tradeType === 'BUY' ? 'text-red' : 'text-blue'">
            {{ summary?.name }} {{ tradeType === 'BUY' ? '매수' : '매도' }}
          </h2>
          <span class="price-tag">현재가 {{ formatPrice(summary?.last_price) }}원</span>
        </div>

        <div class="modal-body">
          <div class="input-section">
            <label>주문 수량</label>
            <div class="input-wrapper">
              <input 
                v-model.number="tradeQuantity" 
                type="number" 
                placeholder="0" 
                min="1"
                class="trade-input"
              />
              <span class="unit">주</span>
            </div>
          </div>

          <div class="total-preview">
            <div class="preview-row">
              <span>총 주문금액</span>
              <span class="total-value" :class="tradeType === 'BUY' ? 'text-red' : 'text-blue'">
                {{ formatPrice((summary?.last_price || 0) * (tradeQuantity || 0)) }}원
              </span>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="showTradeModal = false" class="btn-cancel">취소</button>
          <button 
            @click="executeTrade" 
            class="btn-confirm" 
            :class="tradeType === 'BUY' ? 'buy-bg' : 'sell-bg'"
          >
            {{ tradeType === 'BUY' ? '매수 확인' : '매도 확인' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-detail { background: #000; min-height: 100vh; color: #fff; padding-bottom: 60px; font-family: 'Pretendard', sans-serif; }

/* Hero Header */
.detail-header-hero { position: relative; height: 400px; display: flex; align-items: flex-end; overflow: hidden; }
.hero-bg { position: absolute; inset: 0; background-size: cover; background-position: center; filter: brightness(0.35); }
.hero-gradient { position: absolute; inset: 0; background: linear-gradient(to top, #000 0%, transparent 100%); }
.hero-content { position: relative; z-index: 10; max-width: 1200px; margin: 0 auto; width: 100%; padding: 0 20px 40px; }
.hero-top-nav { margin-bottom: 40px; }
.back-btn { background: none; border: none; color: #fff; cursor: pointer; font-size: 16px; opacity: 0.7; }
.hero-main-info { display: flex; justify-content: space-between; align-items: flex-end; }

/* 타이틀 행 */
.name-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.stock-title { font-size: 38px; font-weight: 800; margin: 0; }
.star-btn { background: none; border: none; color: #ff9d00; font-size: 32px; cursor: pointer; padding: 0; margin-top: 4px; transition: transform 0.2s; line-height: 1; }
.star-btn:hover { transform: scale(1.1); }
.warning-badge { background: rgba(240, 68, 82, 0.2); color: #f04452; padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: bold; margin-left: 10px; }

.price-info { display: flex; align-items: baseline; gap: 15px; margin-top: 10px; }
.main-price { font-size: 42px; font-weight: 900; }
.main-rate { font-size: 22px; font-weight: bold; }

.header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 15px; }
.mileage-info { text-align: right; }
.mileage-label { font-size: 12px; color: #999; margin-bottom: 4px; display: block; }
.mileage-badge { background: #1a1a1b; padding: 10px 20px; border-radius: 12px; color: #fbbf24; font-weight: 800; border: 1px solid #333; font-size: 18px; }
.action-btns { display: flex; gap: 10px; }
.btn { padding: 14px 35px; border-radius: 16px; border: none; font-weight: bold; cursor: pointer; color: #fff; font-size: 17px; }

/* 내비게이션 */
.toss-nav { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; gap: 30px; border-bottom: 1px solid #1a1a1b; }
.toss-nav button { background: none; border: none; color: #666; font-size: 17px; font-weight: bold; padding: 15px 5px; cursor: pointer; border-bottom: 3px solid transparent; transition: 0.2s; }
.toss-nav button.active { color: #fff; border-bottom-color: #fff; }

/* 메인 그리드 */
.main-grid { max-width: 1200px; margin: 40px auto 0; display: grid; grid-template-columns: 8.5fr 3.5fr; gap: 30px; padding: 0 20px; }
.shadow-card { background: #111; border-radius: 28px; padding: 30px; border: 1px solid #222; }

/* 차트 섹션 헤더 */
.card-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 25px; 
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.label-text { 
  font-size: 15px; 
  color: #3182f6; 
  font-weight: bold; 
  margin: 0;
}

/* 인라인 보조 지표 버튼 */
.indicator-tabs-inline { 
  display: flex; 
  gap: 6px; 
}

.indicator-tabs-inline button { 
  background: #1a1a1b; 
  border: 1px solid #333; 
  color: #999; 
  padding: 6px 14px; 
  border-radius: 8px; 
  cursor: pointer; 
  font-size: 12px; 
  font-weight: 600;
  transition: all 0.2s;
}

.indicator-tabs-inline button:hover { 
  background: #222; 
  color: #fff; 
}

.indicator-tabs-inline button.active { 
  background: #3182f6; 
  color: #fff; 
  border-color: #3182f6;
}

.indicator-tabs-inline button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.range-tabs { 
  display: flex; 
  background: #000; 
  padding: 5px; 
  border-radius: 12px; 
  border: 1px solid #222; 
}

.range-tabs button { 
  background: none; 
  border: none; 
  color: #555; 
  padding: 8px 16px; 
  border-radius: 8px; 
  cursor: pointer; 
  font-size: 12px; 
  font-weight: bold; 
  transition: all 0.2s; 
}

.range-tabs button.active { 
  background: #1a1a1b; 
  color: #fff; 
}

/* 로딩 상태 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  gap: 16px;
}

.loading-state p {
  color: #999;
  font-size: 14px;
}

/* 거래량 섹션 */
.volume-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #222;
}

.volume-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.volume-label {
  font-size: 13px;
  color: #999;
  font-weight: 600;
}

/* x축 라벨 스타일 */
:deep(.apexcharts-xaxis-label) {
  font-size: 11px !important;
  fill: #777 !important;
}

:deep(.apexcharts-xaxis text) {
  font-size: 11px !important;
}

/* 커뮤니티 아이템 */
.post-item.clickable { 
  cursor: pointer; 
  transition: all 0.2s ease-in-out; 
  padding: 24px 20px; 
  margin: 0 -20px; 
  border-radius: 20px; 
  border-bottom: 1px solid #222;
}
.post-item.clickable:hover { background: rgba(255, 255, 255, 0.05); transform: translateX(5px); }
.post-meta { display: flex; gap: 10px; font-size: 13px; color: #666; margin-bottom: 10px; }
.post-text { 
  font-size: 16px; 
  line-height: 1.6; 
  color: #ddd; 
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
.more-label { display: inline-block; font-size: 13px; color: #3182f6; font-weight: bold; margin-bottom: 15px; opacity: 0.8; }
.post-stats { display: flex; gap: 15px; font-size: 13px; color: #888; }
.stat-item { display: inline-flex; align-items: center; gap: 4px; }

/* 거래 내역 */
.log-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 25px; }
.log-header h3 { margin: 0; font-size: 15px; color: #3182f6; font-weight: bold; }
.log-list { max-height: 550px; overflow-y: auto; padding-right: 5px; }
.log-item-v2 { padding: 18px 0; border-bottom: 1px solid #222; }
.item-top { display: flex; justify-content: space-between; margin-bottom: 8px; }
.item-bottom { display: flex; justify-content: space-between; align-items: center; }
.type-tag { padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; }
.type-tag.buy { background: rgba(240, 68, 82, 0.2); color: #f04452; }
.type-tag.sell { background: rgba(49, 130, 246, 0.2); color: #3182f6; }
.time { font-size: 12px; color: #666; }
.quantity { font-size: 13px; color: #999; }
.total-amount { font-size: 15px; font-weight: bold; }

/* 모달 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(8px); display: flex; justify-content: center; align-items: center; z-index: 3000; }
.modal-content { background: #1c1c1e; width: 400px; border-radius: 28px; padding: 32px; border: 1px solid #333; }
.modal-header h2 { font-size: 24px; font-weight: 800; margin-bottom: 4px; }
.price-tag { color: #8e8e93; font-size: 14px; }
.modal-body { margin: 24px 0; }
.input-section { margin-bottom: 20px; }
.input-section label { font-size: 13px; color: #999; display: block; margin-bottom: 10px; }
.input-wrapper { position: relative; display: flex; align-items: center; }
.trade-input { background: #2c2c2e; border: 1px solid #3a3a3c; border-radius: 16px; padding: 16px 20px; width: 100%; color: #fff; font-size: 20px; font-weight: bold; text-align: right; padding-right: 50px; outline: none; }
.trade-input:focus { border-color: #3182f6; }
.unit { position: absolute; right: 20px; color: #999; font-weight: bold; }
.total-preview { background: #2c2c2e; padding: 16px; border-radius: 16px; margin-bottom: 32px; }
.preview-row { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: #999; }
.total-value { font-size: 18px; font-weight: 800; }
.modal-footer { display: flex; gap: 12px; }
.btn-cancel { flex: 1; background: #3a3a3c; color: #fff; border: none; padding: 16px; border-radius: 16px; font-weight: bold; cursor: pointer; transition: opacity 0.2s; }
.btn-cancel:hover { opacity: 0.8; }
.btn-confirm { flex: 2; border: none; color: #fff; padding: 16px; border-radius: 16px; font-weight: bold; cursor: pointer; transition: opacity 0.2s; }
.btn-confirm:hover { opacity: 0.9; }

/* 공용 유틸리티 */
.text-red { color: #f04452; }
.text-blue { color: #3182f6; }
.text-gray { color: #999; }
.buy-bg { background: #f04452; }
.sell-bg { background: #3182f6; }
.live-dot { width: 10px; height: 10px; background: #4caf50; border-radius: 50%; box-shadow: 0 0 10px #4caf50; }
.empty-state { text-align: center; padding: 60px 20px; color: #666; }
.empty-log { text-align: center; padding: 40px 20px; color: #666; font-size: 14px; }

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #555; }

@media (max-width: 1024px) { 
  .main-grid { grid-template-columns: 1fr; } 
  .detail-header-hero { height: 350px; }
  .stock-title { font-size: 28px; }
  .main-price { font-size: 32px; }
}
</style>