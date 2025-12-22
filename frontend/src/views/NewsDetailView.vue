<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import VueApexCharts from 'vue3-apexcharts'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const newsId = route.params.id

// --- 상태 관리 ---
const news = ref(null)
const similarResult = ref(null)
const loading = ref(true)
const stockList = ref([]) 
const currentStockIndex = ref(0)

const currentStock = computed(() => stockList.value[currentStockIndex.value] || null)

// --- 차트 옵션 (주말 제거 로직 및 디자인 통합) ---
const chartOptions = computed(() => {
  const stock = currentStock.value
  return {
    chart: { 
      type: 'candlestick', 
      background: 'transparent', 
      toolbar: { show: false },
      animations: { enabled: true, speed: 800 } 
    },
    theme: { mode: 'dark' },
    // ✅ 주말 공백 제거를 위한 Category 타입 유지
    xaxis: {
      type: 'category',
      labels: { 
        style: { colors: '#777', fontSize: '11px' },
        formatter: (val) => dayjs(val).isValid() ? dayjs(val).format('MM/DD') : val
      },
      axisBorder: { show: false },
      tooltip: { enabled: false }
    },
    yaxis: { 
      opposite: true, 
      labels: { 
        style: { colors: '#777' }, 
        formatter: (v) => v?.toLocaleString() 
      } 
    },
    grid: { borderColor: '#222', strokeDashArray: 4 },
    plotOptions: {
      candlestick: { 
        colors: { upward: '#f04452', downward: '#3182f6' },
        wick: { useFillColor: true }
      }
    },
    // ✅ 뉴스 발생 시점 표시 (가로 뱃지 스타일로 시인성 개선)
    annotations: {
      xaxis: stock ? [{
        x: stock.annotationX,
        borderColor: '#f04452',
        borderWidth: 2,
        strokeDashArray: 5,
        label: {
          text: '과거 사례 발생 🚨',
          orientation: 'horizon',
          style: { 
            color: '#fff', 
            background: '#f04452', 
            fontSize: '11px', 
            fontWeight: 'bold',
            padding: { left: 8, right: 8, top: 4, bottom: 4 }
          },
          offsetY: 0
        }
      }] : []
    },
    tooltip: { theme: 'dark' }
  }
})

// --- 데이터 처리 로직 ---
const processChartData = (rawChartData, newsDateStr) => {
  if (!rawChartData || rawChartData.length === 0) return null
  
  // 1. 데이터를 차트 형식에 맞게 변환
  const candles = rawChartData.map(item => ({
    x: dayjs(item.record_time).format('MM/DD'),
    y: [item.open, item.high, item.low, item.close],
    originalDate: item.record_time.substring(0, 10)
  }))

  // 2. 뉴스 발생 날짜와 가장 가까운 인덱스 탐색 (세로선 위치)
  let idx = candles.findIndex(c => c.originalDate >= newsDateStr)
  if (idx === -1) idx = candles.length - 1

  return { 
    series: [{ name: '주가', data: candles }], 
    annotationX: candles[idx].x 
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    const [newsRes, simRes] = await Promise.all([
      axios.get(`http://localhost:8000/api/latest-news/${newsId}/`),
      axios.get(`http://localhost:8000/api/latest-news/${newsId}/similar_historical/`)
    ])

    news.value = newsRes.data
    if (simRes.data.similar_news) {
      similarResult.value = simRes.data
      const dateStr = simRes.data.similar_news.news_collection_date.substring(0, 10)
      
      // 관련 종목별 차트 데이터 가공
      simRes.data.related_stocks?.forEach(s => {
        const proc = processChartData(s.chart_data, dateStr)
        if (proc) {
          stockList.value.push({
            name: s.name,
            ticker: s.ticker,
            ...proc
          })
        }
      })
    }
  } catch (e) {
    console.error("Data Fetch Error:", e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)

const prevStock = () => { if (currentStockIndex.value > 0) currentStockIndex.value-- }
const nextStock = () => { if (currentStockIndex.value < stockList.value.length - 1) currentStockIndex.value++ }
const goToPastNews = () => window.open(similarResult.value.similar_news.url, '_blank')
</script>

<template>
  <div class="report-wrapper">
    <div v-if="loading" class="loading-overlay">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <template v-else-if="news">
      <header class="hero-section">
        <div class="hero-blur-bg" :style="{ backgroundImage: `url(${news.image_url})` }"></div>
        <div class="hero-gradient"></div>
        <div class="hero-inner">
          <v-btn icon="mdi-arrow-left" variant="text" color="white" @click="router.back()" class="mb-6"></v-btn>
          <div class="news-meta">
            <span class="source-tag">{{ news.source }}</span>
            <span class="date-tag">{{ dayjs(news.news_collection_date).format('YYYY.MM.DD HH:mm') }}</span>
          </div>
          <h1 class="main-title">{{ news.title }}</h1>
        </div>
      </header>

      <div class="report-grid">
        <div class="main-column">
          <section class="content-card article-body">
            <h3 class="label-text">주요 브리핑</h3>
            <p class="body-text">{{ news.body }}</p>
            <v-btn variant="outlined" color="primary" :href="news.url" target="_blank" class="mt-6 rounded-lg">
              기사 원문 읽기 <v-icon size="small" class="ml-2">mdi-open-in-new</v-icon>
            </v-btn>
          </section>

          <section class="content-card chart-area" v-if="similarResult">
            <div class="card-header">
              <h3 class="label-text">🤖 과거 주식차트</h3>
              <div class="stock-switcher" v-if="stockList.length > 1">
                <button @click="prevStock" :disabled="currentStockIndex === 0">〈</button>
                <span class="stock-name">{{ currentStock?.name }}</span>
                <button @click="nextStock" :disabled="currentStockIndex === stockList.length - 1">〉</button>
              </div>
            </div>
            <div class="chart-box">
              <VueApexCharts v-if="currentStock" :key="currentStock.ticker" type="candlestick" height="350" 
                             :options="chartOptions" :series="currentStock.series" />
              <div v-else class="no-data">차트 데이터를 찾을 수 없습니다.</div>
            </div>
          </section>
        </div>

        <aside class="side-column">
          <div class="side-card summary-info" v-if="similarResult">
            <h3 class="side-label">AI 분석 요약</h3>
            <div class="stat-item">
              <span class="stat-label">사례 유사도</span>
              <span class="stat-value text-primary">{{ (similarResult.similarity_score * 100).toFixed(1) }}%</span>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: similarResult.similarity_score * 100 + '%' }"></div>
              </div>
            </div>
            <div class="stat-item mt-6">
              <span class="stat-label">관련 종목</span>
              <div class="tag-group">
                <v-chip v-for="s in stockList" :key="s.ticker" size="small" color="primary" variant="tonal">{{ s.name }}</v-chip>
              </div>
            </div>
          </div>

          <div class="side-card past-news-link" v-if="similarResult" @click="goToPastNews">
            <h3 class="side-label">유사 과거 기사</h3>
            <div class="past-preview">
              <span class="past-date">{{ similarResult.similar_news.news_collection_date }}</span>
              <h4 class="past-title">{{ similarResult.similar_news.title }}</h4>
              <p class="past-excerpt">{{ similarResult.similar_news.body }}</p>
            </div>
            <div class="hover-action">당시 기사 보기 〉</div>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.report-wrapper { background: #000; min-height: 100vh; color: #fff; padding-bottom: 60px; font-family: 'Pretendard', sans-serif; }

/* 1. Hero Header - 블러 제거 및 높이 최적화 */
.hero-section { 
  position: relative; 
  min-height: 400px; /* 고정 높이 대신 최소 높이 설정 */
  overflow: hidden; 
  display: flex; 
  align-items: flex-end; 
  padding: 60px 5% 40px; 
}
.hero-blur-bg { 
  position: absolute; 
  inset: 0; 
  background-size: cover; 
  background-position: center; 
  filter: brightness(0.3); /* 블러는 제거하고, 글자가 잘 보이게 밝기만 조절 */
  transform: scale(1); /* 블러 제거로 인한 스케일 보정 */
}
.hero-gradient { 
  position: absolute; 
  inset: 0; 
  background: linear-gradient(to top, #000 0%, transparent 100%); 
}
.hero-inner { position: relative; z-index: 10; max-width: 1200px; margin: 0 auto; width: 100%; }
.main-title { font-size: 38px; font-weight: 800; line-height: 1.3; letter-spacing: -1px; margin-top: 20px; word-break: keep-all; }
.source-tag { background: #3182f6; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: bold; margin-right: 12px; }
.date-tag { color: #aaa; font-size: 14px; }

/* 2. Layout Grid - 겹침 현상 해결 및 간격 확보 */
.report-grid { 
  display: grid; 
  grid-template-columns: 1.6fr 0.9fr; 
  gap: 30px; 
  max-width: 1200px; 
  margin: 40px auto 0; /* 마이너스 마진 제거 및 40px 여백 추가 */
  padding: 0 20px; 
  position: relative; 
  z-index: 20; 
}

/* 3. Common Card Styles */
.content-card, .side-card { background: #111; border: 1px solid #222; border-radius: 24px; padding: 28px; margin-bottom: 24px; }
.label-text { font-size: 14px; color: #3182f6; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 20px; }

/* 이하 기존 스타일 유지 */
.body-text { font-size: 17px; line-height: 1.8; color: #ccc; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.stock-switcher { background: #000; padding: 6px 16px; border-radius: 12px; display: flex; align-items: center; gap: 15px; border: 1px solid #222; }
.stock-name { font-weight: bold; font-size: 14px; }
.stock-switcher button { color: #555; transition: 0.2s; }
.stock-switcher button:not(:disabled):hover { color: #fff; }
.side-label { font-size: 18px; font-weight: bold; margin-bottom: 24px; }
.stat-label { font-size: 13px; color: #666; margin-bottom: 8px; display: block; }
.stat-value { font-size: 28px; font-weight: 800; display: block; margin-bottom: 12px; }
.progress-bar { height: 6px; background: #222; border-radius: 10px; overflow: hidden; }
.progress-fill { height: 100%; background: #3182f6; }
.tag-group { display: flex; flex-wrap: wrap; gap: 8px; }
.past-news-link { cursor: pointer; transition: 0.3s; border-top: 4px solid #3182f6; }
.past-news-link:hover { transform: translateY(-5px); background: #161616; }
.past-date { font-size: 12px; color: #555; }
.past-title { font-size: 16px; font-weight: bold; margin: 10px 0; line-height: 1.4; }
.past-excerpt { font-size: 14px; color: #777; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.hover-action { margin-top: 15px; font-size: 12px; color: #3182f6; font-weight: bold; }
.loading-overlay { height: 100vh; display: flex; align-items: center; justify-content: center; background: #000; }

@media (max-width: 960px) {
  .report-grid { grid-template-columns: 1fr; margin-top: 20px; }
  .main-title { font-size: 28px; }
  .hero-section { min-height: 300px; padding-top: 40px; }
}
</style>