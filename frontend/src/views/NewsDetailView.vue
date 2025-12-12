<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import VueApexCharts from 'vue3-apexcharts'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const newsId = route.params.id

// --- 상태 변수 ---
const news = ref(null)
const similarResult = ref(null)
const loading = ref(true)
const isChartReady = ref(false)

// 🔄 여러 종목 관리를 위한 상태
const stockList = ref([]) // { name, ticker, series, annotationX } 형태의 객체 배열
const currentStockIndex = ref(0) // 현재 보고 있는 종목의 인덱스

// 현재 선택된 종목 데이터 (Computed)
const currentStock = computed(() => {
  if (stockList.value.length === 0) return null
  return stockList.value[currentStockIndex.value]
})

// --- 차트 옵션 (공통) ---
const baseChartOptions = {
  chart: {
    type: 'candlestick',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: true, dynamicAnimation: { enabled: true, speed: 350 } }
  },
  theme: { mode: 'dark' },
  grid: { borderColor: '#333' },
  xaxis: {
    type: 'category', 
    labels: {
      style: { colors: '#888' },
      rotate: -45,
      formatter: (val) => dayjs(val).isValid() ? dayjs(val).format('MM/DD') : val
    },
    tooltip: { enabled: false }
  },
  yaxis: {
    tooltip: { enabled: true },
    labels: { 
      style: { colors: '#888' }, 
      formatter: (val) => val.toLocaleString() 
    }
  },
  plotOptions: {
    candlestick: { colors: { upward: '#00E396', downward: '#FF4560' } }
  },
  tooltip: {
    theme: 'dark',
    x: {
      formatter: function(val, { dataPointIndex, w }) {
        const data = w.config.series[0].data[dataPointIndex]
        return data ? data.originalDate : val
      }
    }
  }
}

// 반응형 차트 옵션 (세로선 포함)
const chartOptions = computed(() => {
  const stock = currentStock.value
  if (!stock) return baseChartOptions

  return {
    ...baseChartOptions,
    annotations: {
      xaxis: [
        {
          x: stock.annotationX, // 현재 종목에 맞는 세로선 위치
          borderColor: '#FF4560',
          borderWidth: 2,
          strokeDashArray: 4, // 점선
          opacity: 1,
          label: {
            text: '뉴스 발생 🚨',
            borderColor: '#FF4560',
            orientation: 'horizontal', // 가로 배치
            position: 'top',
            offsetY: 10,
            style: {
              color: '#fff',
              background: '#FF4560',
              fontSize: '12px',
              fontWeight: 'bold',
              padding: { left: 8, right: 8, top: 4, bottom: 4 }
            }
          }
        }
      ]
    }
  }
})

// --- 네비게이션 함수 ---
const prevStock = () => {
  if (currentStockIndex.value > 0) currentStockIndex.value--
}

const nextStock = () => {
  if (currentStockIndex.value < stockList.value.length - 1) currentStockIndex.value++
}

// 🔗 과거 뉴스로 이동
const goToPastNews = () => {
  if (similarResult.value?.similar_news?.url) {
    window.open(similarResult.value.similar_news.url, '_blank') 
  }
}

// --- 데이터 처리 ---
const processChartData = (rawChartData, newsDateStr) => {
  if (!rawChartData || rawChartData.length === 0) return null

  // 1. 데이터 변환 (x를 단순 문자열로)
  const candles = rawChartData.map(item => {
    const fullDate = item.record_time.substring(0, 10)
    return {
      x: dayjs(fullDate).format('MM/DD'), 
      y: [Number(item.open), Number(item.high), Number(item.low), Number(item.close)],
      originalDate: fullDate 
    }
  })

  // 2. 세로선 위치 찾기
  let targetIndex = candles.findIndex(c => c.originalDate >= newsDateStr)
  if (targetIndex === -1) targetIndex = candles.length - 1

  return {
    series: [{ name: '주가', data: candles }],
    annotationX: candles[targetIndex].x
  }
}

const fetchData = async () => {
  try {
    loading.value = true
    isChartReady.value = false
    stockList.value = [] // 초기화

    const [newsRes, simRes] = await Promise.all([
      axios.get(`http://localhost:8000/api/latest-news/${newsId}/`),
      axios.get(`http://localhost:8000/api/latest-news/${newsId}/similar_historical/`)
    ])

    news.value = newsRes.data

    if (simRes.data.similar_news) {
      similarResult.value = simRes.data
      const newsDateStr = simRes.data.similar_news.news_collection_date.substring(0, 10)
      
      const relatedStocks = simRes.data.related_stocks || []
      
      relatedStocks.forEach(stockData => {
        const processed = processChartData(stockData.chart_data, newsDateStr)
        
        if (processed) {
          stockList.value.push({
            name: stockData.name,    
            ticker: stockData.ticker, 
            series: processed.series,
            annotationX: processed.annotationX
          })
        }
      })

      if (stockList.value.length > 0) {
        isChartReady.value = true
      }
    }

  } catch (error) {
    console.error("데이터 로딩 실패:", error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <v-container class="py-8" style="max-width: 1200px;">
    
    <v-btn variant="text" color="grey" prepend-icon="mdi-arrow-left" @click="router.back()" class="mb-4">
      목록으로
    </v-btn>

    <div v-if="loading" class="d-flex justify-center my-10">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
    </div>

    <div v-else-if="news">
      <v-row>
        <v-col cols="12">
          <h1 class="text-h4 font-weight-bold text-white mb-3">{{ news.title }}</h1>
          <div class="d-flex align-center gap-2 mb-6">
            <v-chip color="blue" variant="tonal" size="small">{{ news.company_name }}</v-chip>
            <span class="text-grey">{{ news.source }} · {{ dayjs(news.news_collection_date).format('YYYY-MM-DD HH:mm') }}</span>
          </div>
          
          <v-card color="#1e1e1e" class="pa-5" rounded="xl" elevation="0">
            <div class="d-flex">
              <v-img v-if="news.image_url" :src="news.image_url" max-width="200" rounded="lg" class="mr-4" cover></v-img>
              <div class="w-100">
                <p class="text-body-1 text-grey-lighten-1" style="line-height: 1.8;">{{ news.body }}</p>
                <v-btn :href="news.url" target="_blank" color="primary" variant="text" class="px-0 mt-2" append-icon="mdi-open-in-new">
                  원본 기사 보러가기
                </v-btn>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4" v-if="similarResult">
        <v-col cols="12">
          <h3 class="text-h5 font-weight-bold text-white mb-4">
            🤖 AI 과거 사례 분석
          </h3>
          <p class="text-grey mb-4">
            이 뉴스와 가장 유사한 과거 사례는 
            <span class="text-primary font-weight-bold">{{ similarResult.similar_news.news_collection_date }}</span>에 발생했습니다.<br>
            (유사도: {{ (similarResult.similarity_score * 100).toFixed(1) }}%)
          </p>

          <v-row>
            <v-col cols="12" md="8">
              <v-card color="#141414" variant="outlined" class="pa-4 h-100" rounded="xl">
                
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="d-flex align-center">
                    
                    <v-btn 
                      icon="mdi-chevron-left" 
                      variant="text" 
                      color="grey"
                      density="comfortable"
                      :disabled="currentStockIndex === 0"
                      @click="prevStock"
                    ></v-btn>

                    <h4 class="text-h6 font-weight-bold text-white mx-2" v-if="currentStock">
                      📉 당시 {{ currentStock.name }} 주가 흐름
                      <span class="text-caption text-grey ml-1">({{ currentStock.ticker }})</span>
                    </h4>

                    <v-btn 
                      icon="mdi-chevron-right" 
                      variant="text" 
                      color="grey"
                      density="comfortable"
                      :disabled="currentStockIndex === stockList.length - 1"
                      @click="nextStock"
                    ></v-btn>
                  </div>

                  <v-chip color="orange" variant="flat" size="small">과거 데이터</v-chip>
                </div>
                
                <div v-if="isChartReady && currentStock">
                  <VueApexCharts 
                    :key="currentStock.ticker" 
                    type="candlestick" 
                    height="350" 
                    :options="chartOptions" 
                    :series="currentStock.series" 
                  />
                </div>
                <div v-else class="text-center py-10 text-grey">
                  해당 기간의 주가 데이터가 없습니다.
                </div>
              </v-card>
            </v-col>

            <v-col cols="12" md="4">
              <v-hover v-slot="{ isHovering, props }">
                <v-card 
                  v-bind="props"
                  color="#2a2a2a" 
                  class="pa-6 h-100 cursor-pointer transition-swing d-flex flex-column" 
                  :class="{ 'on-hover': isHovering }"
                  :elevation="isHovering ? 8 : 0"
                  rounded="xl" 
                  @click="goToPastNews"
                >
                  <div class="d-flex justify-space-between align-center mb-4">
                    <v-chip color="grey-lighten-1" size="small" variant="flat" class="font-weight-bold text-black">
                      유사 뉴스
                    </v-chip>
                    <v-icon color="grey" v-if="isHovering">mdi-arrow-right</v-icon>
                  </div>
                  
                  <h4 class="text-h6 font-weight-bold text-white mb-4" style="line-height: 1.4;">
                    {{ similarResult.similar_news.title }}
                  </h4>

                  <p class="text-body-2 text-grey-lighten-1 mb-auto text-truncate-expanded">
                    {{ similarResult.similar_news.body }}
                  </p>
                  
                  <v-divider class="my-4"></v-divider>
                  
                  <div class="text-caption text-grey d-flex align-center">
                    <v-icon icon="mdi-domain" size="small" class="mr-1"></v-icon>
                    관련 종목: 
                    <span v-if="stockList.length > 0" class="ml-1 text-white font-weight-medium">
                      {{ stockList.map(s => s.name).join(', ') }}
                    </span>
                    <span v-else class="ml-1 text-white font-weight-medium">
                      {{ similarResult.company_name }}
                    </span>
                  </div>
                </v-card>
              </v-hover>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      
      <v-row v-else class="mt-4">
        <v-col cols="12">
           <v-alert type="info" variant="tonal" color="grey">
             아직 분석 가능한 유사 과거 데이터가 충분하지 않습니다.
           </v-alert>
        </v-col>
      </v-row>

    </div>
  </v-container>
</template>

<style scoped>
/* 텍스트 내용 12줄로 확장 */
.text-truncate-expanded {
  display: -webkit-box;
  -webkit-line-clamp: 12;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.6;
}

.cursor-pointer {
  cursor: pointer;
}
/* 호버 시 배경색 살짝 밝게 */
.on-hover {
  background-color: #333333 !important;
}

.news-item-card {
  /* 👇 [추가] 높이를 강제로 고정해서 내용물 변화에 따른 떨림 방지 */
  height: 160px; 
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>