<!-- frontend/src/views/HomeView.vue -->
<script setup>
const marketSummary = [
  {
    label: '코스피',
    value: '2,645.57',
    diff: '+1.2%',
  },
  {
    label: '코스닥',
    value: '878.45',
    diff: '+0.8%',
  },
  {
    label: '환율 (USD)',
    value: '1,324.50',
    diff: '-0.3%',
  },
]

const popularStocks = [
  {
    rank: 1,
    name: '삼성전자',
    code: '005930',
    price: '71,800',
    change: '+2.3%',
    changeAbs: '+1,600',
    volume: '15.2M',
    trend: 'up',
  },
  {
    rank: 2,
    name: 'SK하이닉스',
    code: '000660',
    price: '142,500',
    change: '-5.7%',
    changeAbs: '-7,700',
    volume: '8.3M',
    trend: 'down',
  },
  {
    rank: 3,
    name: 'LG에너지솔루션',
    code: '373220',
    price: '385,000',
    change: '+1.2%',
    changeAbs: '+4,700',
    volume: '3.1M',
    trend: 'up',
  },
  {
    rank: 4,
    name: '카카오',
    code: '035720',
    price: '45,600',
    change: '+3.4%',
    changeAbs: '+1,600',
    volume: '12.5M',
    trend: 'up',
  },
  {
    rank: 5,
    name: 'NAVER',
    code: '035420',
    price: '198,500',
    change: '-1.8%',
    changeAbs: '-3,500',
    volume: '5.7M',
    trend: 'down',
  },
]
</script>

<template>
  <div class="home">
    <!-- 상단 마켓 요약 카드 -->
    <section class="hero">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-title-block">
          <p class="hero-subtitle">오늘의 국내 시장 한눈에 보기</p>
          <h1 class="hero-title">
            AI와 함께 하는<br />
            나만의 주식 코치
          </h1>
          <p class="hero-desc">
            뉴스·커뮤니티·내 포트폴리오를 한 번에 분석해서<br />
            초보 투자자도 쉽게 따라올 수 있는 인사이트를 제공합니다.
          </p>
        </div>

        <div class="hero-cards">
          <div
            v-for="card in marketSummary"
            :key="card.label"
            class="hero-card"
          >
            <p class="card-label">{{ card.label }}</p>
            <p class="card-value">{{ card.value }}</p>
            <p
              class="card-diff"
              :class="{ positive: card.diff.startsWith('+'), negative: card.diff.startsWith('-') }"
            >
              {{ card.diff }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- 인기 종목 테이블 -->
    <section class="section">
      <div class="section-header">
        <h2 class="section-title">실시간 인기 종목</h2>
        <p class="section-subtitle">투자자들이 많이 보고 있는 종목을 확인해보세요.</p>
      </div>

      <div class="table-card">
        <table class="stock-table">
          <thead>
            <tr>
              <th class="col-rank">순위</th>
              <th class="col-name">종목명</th>
              <th class="col-price">현재가</th>
              <th class="col-change">전일대비</th>
              <th class="col-volume">거래량</th>
              <th class="col-chart">차트</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="stock in popularStocks"
              :key="stock.rank"
            >
              <td class="col-rank">
                <span class="rank-badge">{{ stock.rank }}</span>
              </td>
              <td class="col-name">
                <div class="name-wrapper">
                  <span class="name">{{ stock.name }}</span>
                  <span class="code">{{ stock.code }}</span>
                </div>
              </td>
              <td class="col-price">
                {{ stock.price }}
              </td>
              <td class="col-change">
                <div
                  class="change-chip"
                  :class="{
                    up: stock.change.startsWith('+'),
                    down: stock.change.startsWith('-'),
                  }"
                >
                  <span class="change-main">{{ stock.change }}</span>
                  <span class="change-abs">{{ stock.changeAbs }}</span>
                </div>
              </td>
              <td class="col-volume">
                {{ stock.volume }}
              </td>
              <td class="col-chart">
                <div
                  class="mini-chart"
                  :class="stock.trend"
                >
                  <span class="line"></span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* 상단 메인 카드 */
.hero {
  position: relative;
  border-radius: 24px;
  overflow: hidden;
  padding: 24px 24px 20px;
  background: radial-gradient(circle at 0% 0%, #3b82f6 0, transparent 55%),
    radial-gradient(circle at 100% 0%, #a855f7 0, transparent 55%),
    radial-gradient(circle at 50% 100%, #22c55e 0, transparent 55%),
    #0b1020;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 0 0, rgba(255, 255, 255, 0.08) 0, transparent 55%);
  opacity: 0.5;
  pointer-events: none;
}

.hero-content {
  position: relative;
  display: flex;
  justify-content: space-between;
  gap: 32px;
}

.hero-title-block {
  max-width: 360px;
}

.hero-subtitle {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.8;
  margin-bottom: 6px;
}

.hero-title {
  font-size: 24px;
  line-height: 1.4;
  font-weight: 800;
  margin: 0 0 10px;
}

.hero-desc {
  font-size: 13px;
  line-height: 1.5;
  color: #e5e7eb;
  opacity: 0.9;
}

.hero-cards {
  display: flex;
  gap: 14px;
  align-items: stretch;
  min-width: 0;
}

.hero-card {
  flex: 1;
  padding: 14px 14px 12px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.86);
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.7);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-label {
  font-size: 12px;
  color: #9ca3af;
}

.card-value {
  font-size: 20px;
  font-weight: 700;
}

.card-diff {
  font-size: 12px;
  font-weight: 600;
}

.card-diff.positive {
  color: #22c55e;
}

.card-diff.negative {
  color: #f97373;
}

/* 섹션 */
.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
}

.section-subtitle {
  font-size: 13px;
  color: #9ca3af;
}

/* 테이블 카드 */
.table-card {
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 0 18px 45px rgba(0, 0, 0, 0.75);
  overflow: hidden;
}

.stock-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.stock-table thead {
  background: rgba(15, 23, 42, 0.96);
}

.stock-table th,
.stock-table td {
  padding: 10px 14px;
  text-align: left;
}

.stock-table th {
  font-weight: 600;
  color: #9ca3af;
  border-bottom: 1px solid rgba(148, 163, 184, 0.3);
}

.stock-table tbody tr:nth-child(even) {
  background: rgba(15, 23, 42, 0.88);
}

.stock-table tbody tr:hover {
  background: rgba(30, 64, 175, 0.4);
}

/* 컬럼 너비 */
.col-rank {
  width: 60px;
}

.col-name {
  width: 220px;
}

.col-price {
  width: 120px;
}

.col-change {
  width: 160px;
}

.col-volume {
  width: 120px;
}

.col-chart {
  width: 120px;
}

/* 각 셀 요소 */
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.6);
  font-size: 12px;
}

.name-wrapper {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.name {
  font-weight: 600;
}

.code {
  font-size: 11px;
  color: #9ca3af;
}

.col-price {
  font-weight: 600;
}

.change-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(15, 23, 42, 0.9);
}

.change-chip.up {
  color: #4ade80;
}

.change-chip.down {
  color: #f97373;
}

.change-abs {
  font-size: 11px;
  opacity: 0.85;
}

/* 미니 차트 (간단한 비주얼용) */
.mini-chart {
  height: 26px;
  border-radius: 999px;
  background: radial-gradient(circle at 0 100%, rgba(148, 163, 184, 0.4), transparent 55%);
  position: relative;
  overflow: hidden;
}

.mini-chart .line {
  position: absolute;
  inset: 5px 6px;
  border-radius: 999px;
  border-width: 2px;
  border-style: solid;
  border-color: transparent;
}

.mini-chart.up .line {
  border-image: linear-gradient(90deg, #22c55e, #4ade80) 1;
}

.mini-chart.down .line {
  border-image: linear-gradient(90deg, #f97373, #fb923c) 1;
}

/* 반응형 */
@media (max-width: 900px) {
  .hero-content {
    flex-direction: column;
  }

  .hero-cards {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .hero {
    padding: 18px 16px;
  }

  .hero-title {
    font-size: 20px;
  }

  .section-title {
    font-size: 16px;
  }

  .stock-table th:nth-child(5),
  .stock-table td:nth-child(5),
  .stock-table th:nth-child(6),
  .stock-table td:nth-child(6) {
    display: none;
  }
}
</style>
