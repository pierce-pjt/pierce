<!-- frontend/src/views/HomeView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 💡 여기서는 "어떤 종목을 보여줄지"만 프론트에서 관리하고
// 실제 가격/등락률/거래량/차트 데이터는 전부 백엔드에서 가져온다.
const TICKERS = [
  { code: '005930', name: '삼성전자' },
  { code: '000660', name: 'SK하이닉스' },
  { code: '373220', name: 'LG에너지솔루션' },
  { code: '035720', name: '카카오' },
  { code: '035420', name: 'NAVER' },
  { code: '005380', name: '현대차' },
  { code: '068270', name: '셀트리온' },
  { code: '000270', name: '기아' },
]

const stocks = ref([])        // 백엔드에서 받아온 실시간 종목 데이터
const loading = ref(false)
const errorMessage = ref('')

// 백엔드 API 기본 주소 (리버스프록시/Nginx 쓰면 '/api' 만 남겨도 됨)
const API_BASE = '/api'

const goStockDetail = (stock) => {
  router.push(`/stock/${stock.code}`)
}

const getChartPoints = (data) => {
  if (!data || data.length < 2) return ''

  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1

  return data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * 80
      const y = 40 - ((value - min) / range) * 40
      return `${x},${y}`
    })
    .join(' ')
}

// 🔌 백엔드에서 요약 + 차트 데이터 불러오기
const fetchStocks = async () => {
  loading.value = true
  errorMessage.value = ''
  const results = []

  try {
    // 각 티커별로 summary + chart 2개의 엔드포인트를 호출한다.
    for (const item of TICKERS) {
      const code = item.code

      // 1) 요약 정보 (/api/stock-prices/summary/?ticker=005930)
      const summaryRes = await fetch(
        `${API_BASE}/stock-prices/summary/?ticker=${code}`,
      )

      if (!summaryRes.ok) {
        // 데이터 없는 종목은 그냥 건너뜀
        continue
      }

      const summary = await summaryRes.json()

      // 2) 최근 7일 차트 (/api/stock-prices/chart/?ticker=005930&days=7)
      const chartRes = await fetch(
        `${API_BASE}/stock-prices/chart/?ticker=${code}&days=7`,
      )
      let chartData = []
      if (chartRes.ok) {
        const chartJson = await chartRes.json()
        // close 가격만 꺼내서 간단한 라인차트용 데이터로 사용
        chartData = chartJson.map((row) => Number(row.close))
      }

      results.push({
        name: item.name,
        code,
        // 백엔드 summary View에서 내려주는 필드 이름에 맞춰서 사용
        price: summary.last_price ?? 0,
        change: summary.change_rate ?? 0,
        changeAmount: summary.change ?? 0,
        volume: summary.volume ?? 0,
        chartData,
      })
    }

    // 거래량 기준 내림차순 정렬 후 순위 부여
    results.sort((a, b) => Number(b.volume) - Number(a.volume))
    stocks.value = results.map((s, idx) => ({
      id: idx + 1,
      rank: idx + 1,
      ...s,
    }))
  } catch (err) {
    console.error(err)
    errorMessage.value = '실시간 종목 데이터를 불러오는 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStocks()
})
</script>

<template>
  <div class="home-page">
    <!-- 🔹 상단 3개 마켓 카드 (지금은 임시 정적인 값, 나중에 원하면 이것도 API 연결 가능) -->
    <section class="market-grid">
      <div class="market-card">
        <div class="market-label">코스피</div>
        <div class="market-row">
          <div class="market-value">2,645.57</div>
          <div class="market-change market-change-up">
            <span class="arrow">▲</span>
            <span class="market-change-text">+1.2%</span>
          </div>
        </div>
      </div>

      <div class="market-card">
        <div class="market-label">코스닥</div>
        <div class="market-row">
          <div class="market-value">878.45</div>
          <div class="market-change market-change-up">
            <span class="arrow">▲</span>
            <span class="market-change-text">+0.8%</span>
          </div>
        </div>
      </div>

      <div class="market-card">
        <div class="market-label">환율 (USD)</div>
        <div class="market-row">
          <div class="market-value">1,324.50</div>
          <div class="market-change market-change-down">
            <span class="arrow">▼</span>
            <span class="market-change-text">-0.3%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 🔹 에러 메시지 -->
    <p v-if="errorMessage" class="error-text">
      {{ errorMessage }}
    </p>

    <!-- 🔹 인기 종목 테이블 -->
    <section class="stocks-card">
      <div class="stocks-header">
        <h2>실시간 인기 종목</h2>
      </div>

      <div class="stocks-table-wrapper">
        <table class="stocks-table">
          <thead>
            <tr>
              <th class="col-rank">순위</th>
              <th class="col-name">종목명</th>
              <th class="col-price">현재가</th>
              <th class="col-change">전일대비</th>
              <th class="col-volume">거래량</th>
              <th class="col-chart">차트</th>
              <th class="col-star"></th>
            </tr>
          </thead>
          <tbody>
            <!-- 로딩 중일 때 -->
            <tr v-if="loading">
              <td colspan="7" class="loading-cell">
                실시간 종목 데이터를 불러오는 중입니다...
              </td>
            </tr>

            <!-- 데이터가 없을 때 -->
            <tr v-else-if="!stocks.length">
              <td colspan="7" class="loading-cell">
                표시할 종목 데이터가 없습니다.
              </td>
            </tr>

            <!-- 실제 데이터 -->
            <tr
              v-else
              v-for="stock in stocks"
              :key="stock.id"
              class="stock-row"
              @click="goStockDetail(stock)"
            >
              <td class="col-rank">
                <span class="rank-text">{{ stock.rank }}</span>
              </td>

              <td class="col-name">
                <div class="name-block">
                  <div class="name-main">{{ stock.name }}</div>
                  <div class="name-code">{{ stock.code }}</div>
                </div>
              </td>

              <td class="col-price">
                {{ Number(stock.price).toLocaleString() }}
              </td>

              <td class="col-change">
                <div
                  class="change-block"
                  :class="{
                    up: stock.change >= 0,
                    down: stock.change < 0,
                  }"
                >
                  <div class="change-main">
                    <span class="arrow-icon">
                      {{ stock.change >= 0 ? '▲' : '▼' }}
                    </span>
                    <span>{{ Math.abs(Number(stock.change)).toFixed(2) }}%</span>
                  </div>
                  <div class="change-amount">
                    {{ stock.change >= 0 ? '+' : '' }}
                    {{ Number(stock.changeAmount).toLocaleString() }}
                  </div>
                </div>
              </td>

              <td class="col-volume">
                {{ Number(stock.volume).toLocaleString() }}
              </td>

              <td class="col-chart">
                <svg width="80" height="40" class="mini-chart">
                  <polyline
                    :points="getChartPoints(stock.chartData)"
                    fill="none"
                    :class="[
                      'mini-chart-line',
                      stock.change >= 0 ? 'mini-chart-line-up' : 'mini-chart-line-down',
                    ]"
                  />
                </svg>
              </td>

              <td class="col-star" @click.stop>
                <button class="star-btn" type="button">
                  ★
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px 20px 40px;
  color: #f5f5f7;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* 에러 텍스트 */
.error-text {
  margin-bottom: 12px;
  font-size: 13px;
  color: #f97373;
}

/* ----- 상단 마켓 카드 ----- */

.market-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.market-card {
  background: #141414;
  border-radius: 16px;
  padding: 18px 20px;
  border: 1px solid #1f2937;
  box-shadow: 0 16px 30px rgba(0, 0, 0, 0.6);
}

.market-label {
  font-size: 13px;
  color: #9ca3af;
  margin-bottom: 6px;
}

.market-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.market-value {
  font-size: 22px;
  font-weight: 600;
}

.market-change {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 2px;
  font-size: 13px;
  font-weight: 600;
}

.market-change-up {
  color: #ef4444;
}

.market-change-down {
  color: #3b82f6;
}

.arrow {
  font-size: 11px;
}

.market-change-text {
  margin-top: 1px;
}

/* ----- 인기 종목 카드/테이블 ----- */

.stocks-card {
  background: #141414;
  border-radius: 18px;
  border: 1px solid #1f2937;
  overflow: hidden;
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.75);
}

.stocks-header {
  padding: 14px 24px;
  border-bottom: 1px solid #1f2937;
}

.stocks-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.stocks-table-wrapper {
  overflow-x: auto;
}

.stocks-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.stocks-table thead {
  background: #0a0a0a;
}

.stocks-table th,
.stocks-table td {
  padding: 10px 18px;
  text-align: left;
}

.stocks-table th {
  color: #9ca3af;
  font-weight: 500;
}

.col-price,
.col-change,
.col-volume {
  text-align: right;
}

.col-chart {
  text-align: center;
}

.col-star {
  width: 60px;
  text-align: center;
}

/* 순위, 이름 */

.rank-text {
  color: #9ca3af;
}

.name-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.name-main {
  font-weight: 500;
}

.name-code {
  font-size: 11px;
  color: #6b7280;
}

/* 변화율 */

.change-block {
  display: inline-flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 13px;
}

.change-block.up {
  color: #ef4444;
}

.change-block.down {
  color: #3b82f6;
}

.change-main {
  display: flex;
  align-items: center;
  gap: 4px;
}

.change-amount {
  font-size: 11px;
  margin-top: 2px;
  opacity: 0.9;
}

.arrow-icon {
  font-size: 10px;
}

/* 미니 차트 */

.mini-chart {
  opacity: 0.85;
}

.mini-chart-line {
  stroke-width: 2;
}

.mini-chart-line-up {
  stroke: #ef4444;
}

.mini-chart-line-down {
  stroke: #3b82f6;
}

/* 즐겨찾기 스타 */

.star-btn {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, transform 0.05s ease;
}

.star-btn:hover {
  background: #1f2937;
  color: #facc15;
  transform: translateY(-1px);
}

.star-btn:active {
  transform: translateY(0);
}

/* 행 hover 효과 */

.stock-row {
  border-top: 1px solid #1f2937;
  cursor: pointer;
  transition: background 0.12s ease;
}

.stock-row:hover {
  background: #1a1a1a;
}

/* 로딩/빈 상태 셀 */

.loading-cell {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
}

/* 반응형 */

@media (max-width: 900px) {
  .market-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stocks-table th:nth-child(6),
  .stocks-table td:nth-child(6) {
    display: none;
  }
}
</style>
