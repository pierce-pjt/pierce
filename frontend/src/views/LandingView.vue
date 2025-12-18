<script setup>
import { useRouter } from 'vue-router'
//image import
import dataAnalysisImg from '@/assets/data_image.jpeg'
import communityImg from '@/assets/community_image.jpeg'

const router = useRouter()

const goDashboard = () => {
  router.push({ name: 'dashboard' })
}
</script>

<template>
  <div class="landing-container">
    
    <section class="section hero">
      <div class="content">
        <h1 class="main-title">
          주식, 과거부터 현재까지<br />
          <span class="highlight">BackLoop</span>에서
        </h1>
        <p class="sub-text">
          데이터 기반의 스마트한 주식 분석 플랫폼
        </p>
        <button class="start-btn" @click="goDashboard">
          시작하기
        </button>
      </div>
    </section>

    <section class="section feature">
      <div class="feature-card">
        <div class="card-image-wrapper">
          <img :src="dataAnalysisImg" alt="데이터 기반 주식 분석" class="card-image" />
        </div>
        <div class="card-text">
          <h2>데이터 기반 주식 추천</h2>
          <p>과거 데이터를 분석하여<br />합리적인 투자 지표를 제공합니다.</p>
        </div>
      </div>
    </section>

    <section class="section feature">
      <div class="feature-card reverse">
        <div class="card-text">
          <h2>커뮤니티와 함께 성장</h2>
          <p>혼자 고민하지 마세요.<br />다양한 투자자들과 인사이트를 나누세요.</p>
        </div>
        <div class="card-image-wrapper">
          <img :src="communityImg" alt="커뮤니티" class="card-image" />
        </div>
      </div>
    </section>

    <section class="section footer-cta">
      <h2 class="welcome-text">Welcome to<br />Hybrid Stock Service</h2>
      <button class="start-btn outline" @click="goDashboard">
        BackLoop 입장하기
      </button>
    </section>

  </div>
</template>

<style scoped>
/* 기존 스타일 유지 */
.landing-container {
  background-color: #D3E4F5;
  color: #1a1a1a;
  font-family: system-ui, -apple-system, sans-serif;
  min-height: calc(100vh - 64px);
}
.section {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
}
.main-title {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: 24px;
  line-height: 1.2;
}
.highlight { color: #2563eb; }
.sub-text {
  font-size: 1.2rem;
  color: #555;
  margin-bottom: 40px;
}
.start-btn {
  padding: 14px 40px;
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
  background-color: #111;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  transition: transform 0.2s;
}
.start-btn:hover { transform: translateY(-3px); }
.start-btn.outline {
  background: transparent;
  border: 2px solid #111;
  color: #111;
}
.start-btn.outline:hover { background: #111; color: white; }

.feature-card {
  display: flex;
  gap: 60px;
  max-width: 1000px;
  align-items: center;
}
.feature-card.reverse { flex-direction: row-reverse; }
.card-text h2 { font-size: 2.5rem; margin-bottom: 20px; }
.card-text p { font-size: 1.2rem; color: #444; line-height: 1.6; }

/* 이미지 스타일 */
.card-image-wrapper {
  width: 400px;
  height: 300px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  background: #fff; /* 이미지가 투명할 경우를 대비해 흰색 배경 */
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 이미지가 영역을 꽉 채우도록 */
  display: block;
}

.welcome-text { font-size: 3rem; font-weight: 800; text-align: center; margin-bottom: 40px; }
</style>