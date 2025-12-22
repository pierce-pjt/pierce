<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/ko'

dayjs.extend(relativeTime)
dayjs.locale('ko')

const router = useRouter()

// --- 1. 상태 관리 ---
const newsItems = ref([])       
const loading = ref(false)      
const searchQuery = ref('')     
const page = ref(1)             
const totalPages = ref(1)       

const CATEGORIES = ['통합뉴스', '인기뉴스', '최신뉴스', '유사도순']
const activeCategory = ref('통합뉴스')

// --- 2. API 통신 ---
const fetchNews = async () => {
  loading.value = true
  window.scrollTo({ top: 0, behavior: 'smooth' })
  
  try {
    let sortParam = 'latest'

    if (activeCategory.value === '인기뉴스') {
      sortParam = 'popular'
    } else if (activeCategory.value === '유사도순') {
      sortParam = 'similarity'
    } 

    const response = await axios.get('http://localhost:8000/api/latest-news/', {
      params: {
        search: searchQuery.value,
        page: page.value, 
        sort: sortParam,
      }
    })
    
    newsItems.value = response.data.results 
    const totalCount = response.data.count
    totalPages.value = Math.ceil(totalCount / 20)

  } catch (error) {
    console.error('뉴스 불러오기 실패:', error)
  } finally {
    loading.value = false
  }
}

// 🆕 조회수 증가 함수
const incrementViewCount = async (newsId) => {
  try {
    await axios.post(`http://localhost:8000/api/latest-news/${newsId}/increment-view/`)
  } catch (error) {
    console.error('조회수 증가 실패:', error)
  }
}

// 🆕 뉴스 클릭 핸들러
const handleNewsClick = (news) => {
  // 조회수 증가 (백그라운드 처리)
  incrementViewCount(news.id)
  
  // 즉시 상세 페이지로 이동
  router.push({ name: 'news-detail', params: { id: news.id } })
}

// --- 3. 이벤트 핸들러 ---
onMounted(() => {
  fetchNews()
})

watch(page, () => {
  fetchNews()
})

const onSearch = () => {
  page.value = 1 
  fetchNews()
}

const selectCategory = (cat) => {
  activeCategory.value = cat
  page.value = 1
  fetchNews()
}

// --- 유틸리티 함수 ---
const formatTime = (dateString) => {
  if (!dateString) return ''
  return dayjs(dateString).fromNow()
}

const getSentimentColor = (sentiment) => {
  if (sentiment === 'positive') return 'green-accent-3'
  if (sentiment === 'negative') return 'red-accent-2'
  return 'grey'
}

const getSentimentText = (sentiment) => {
  if (sentiment === 'positive') return '호재'
  if (sentiment === 'negative') return '악재'
  return '중립'
}
</script>

<template>
  <v-container class="py-8 pb-16" style="max-width: 1280px;">
    
    <v-row>
      <v-col cols="12" md="3">
        <v-card class="custom-card pa-4" variant="outlined" rounded="xl">
          <h2 class="text-h6 font-weight-bold mb-4 ml-2 text-white">뉴스 분류</h2>
          <v-list bg-color="transparent" class="pa-0">
            <v-list-item
              v-for="category in CATEGORIES"
              :key="category"
              @click="selectCategory(category)"
              rounded="lg"
              class="mb-1"
              :class="{ 'active-category': activeCategory === category }"
              link
            >
              <template v-slot:prepend>
                 <v-icon v-if="category === '인기뉴스'" icon="mdi-fire" color="red" class="mr-2"></v-icon>
                 <v-icon v-if="category === '최신뉴스'" icon="mdi-clock-outline" color="blue" class="mr-2"></v-icon>
                 <v-icon v-if="category === '유사도순'" icon="mdi-vector-link" color="purple" class="mr-2"></v-icon>
                 <v-icon v-if="category === '통합뉴스'" icon="mdi-newspaper" color="grey" class="mr-2"></v-icon>
              </template>

              <v-list-item-title :class="activeCategory === category ? 'text-white font-weight-bold' : 'text-grey'">
                {{ category }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <v-col cols="12" md="9" class="overflow-hidden">
        
        <div class="mb-6">
          <v-text-field
            v-model="searchQuery"
            placeholder="뉴스 키워드 검색 (종목명, 내용 등)"
            variant="outlined"
            prepend-inner-icon="mdi-magnify"
            rounded="xl"
            bg-color="#141414"
            color="primary"
            hide-details
            class="custom-input"
            @keyup.enter="onSearch"
          ></v-text-field>
        </div>

        <div v-if="loading" class="d-flex justify-center my-10">
          <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
        </div>

        <div v-else-if="newsItems.length === 0" class="text-center text-grey my-10">
          <v-icon icon="mdi-newspaper-remove" size="64" class="mb-4"></v-icon>
          <h3 class="text-h6">표시할 뉴스가 없습니다.</h3>
        </div>

        <div v-else class="d-flex flex-column gap-4 mb-16">
          <v-card
            v-for="news in newsItems"
            :key="news.id"
            class="custom-card news-item-card"
            variant="outlined"
            rounded="xl"
            link
            @click="handleNewsClick(news)"
          >
            <div class="d-flex pa-5">
              <div class="thumbnail-box rounded-lg mr-5 d-flex align-center justify-center bg-grey-darken-4 overflow-hidden border-subtle">
                <v-img v-if="news.image_url" :src="news.image_url" cover class="fill-height fill-width transition-swing"></v-img>
                <v-icon v-else icon="mdi-newspaper-variant-outline" color="grey-darken-1" size="32"></v-icon>
              </div>

              <div class="flex-grow-1 d-flex flex-column justify-space-between">
                <div>
                  <h3 class="text-subtitle-1 font-weight-bold text-white mb-2 text-truncate-2 title-hover">
                    {{ news.title }}
                  </h3>
                  
                  <div class="d-flex flex-wrap gap-2 mb-2">
                    <v-chip
                      v-if="news.company_name"
                      size="x-small"
                      color="blue-lighten-1"
                      variant="tonal"
                      label
                      class="font-weight-bold"
                      style="max-width: 120px;" 
                    >
                      <span class="text-truncate">{{ news.company_name }}</span>
                    </v-chip>

                    <v-chip 
                      v-if="news.sentiment && news.sentiment !== 'neutral'" 
                      size="x-small" 
                      :color="getSentimentColor(news.sentiment)" 
                      variant="tonal" 
                      label 
                      class="font-weight-bold" 
                      prepend-icon="mdi-chart-line"
                    >
                      {{ getSentimentText(news.sentiment) }}
                    </v-chip>

                    <v-chip 
                      v-if="activeCategory === '유사도순' && !searchQuery && news.max_similarity_score" 
                      size="x-small" 
                      color="purple" 
                      variant="tonal"
                      label
                      class="font-weight-bold"
                    >
                      역사 유사도 {{ (news.max_similarity_score * 100).toFixed(1) }}%
                    </v-chip>
                  </div>
                </div>

                <div class="d-flex align-center text-caption text-grey">
                  <span class="font-weight-medium text-grey-lighten-2">{{ news.source || '인터넷뉴스' }}</span>
                  <span class="mx-2">·</span>
                  <span>{{ formatTime(news.news_collection_date) }}</span>
                  <span class="mx-2">·</span>
                  <span>조회 {{ news.view_count || 0 }}</span>
                </div>
              </div>
            </div>
          </v-card>
        </div>

      </v-col>
    </v-row>

    <div class="fixed-bottom-pagination" v-if="newsItems.length > 0">
      <div class="d-flex justify-center align-center h-100">
        <v-pagination
          v-model="page"
          :length="totalPages" 
          rounded="circle"
          active-color="primary"
          variant="flat"
          size="small"
        ></v-pagination>
      </div>
    </div>

  </v-container>
</template>

<style scoped>
.custom-card {
  background-color: #141414 !important;
  border-color: #333 !important;
  transition: all 0.2s ease-in-out;
}
.custom-card:hover {
  border-color: #555 !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.active-category {
  background-color: #2a2a2a !important;
}
.custom-input :deep(.v-field__outline__start),
.custom-input :deep(.v-field__outline__end),
.custom-input :deep(.v-field__outline__notch) {
  border-color: #333 !important;
}
.thumbnail-box {
  width: 110px;
  height: 110px;
  flex-shrink: 0;
  border: 1px solid #333;
}
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}
.news-item-card:hover .title-hover {
  text-decoration: underline;
  text-decoration-color: #666;
  text-underline-offset: 4px;
}
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
.border-subtle {
  border: 1px solid rgba(255,255,255,0.1);
}
.mb-16 {
  margin-bottom: 64px !important;
}

/* 스크롤바 유무에 따른 화면 흔들림 방지 */
.v-container {
  min-height: 101vh !important;
}

/* 하단바 고정 및 흔들림 방지 */
.fixed-bottom-pagination {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100% !important; 
  height: 80px;
  background-color: rgba(18, 18, 18, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid #333;
  z-index: 1000;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.5);
}
</style>