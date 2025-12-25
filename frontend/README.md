# 📈 BackLoop: 과거 뉴스 데이터 기반 주식 추천 플랫폼  
> **“과거가 들려주는 미래의 힌트, BackLoop”**

BackLoop는 단순히 정보를 나열하는 것을 넘어, **과거 뉴스 데이터와 주가 변동 이력**을 정밀 분석하여 **현재의 뉴스가 시장에 미칠 영향을 데이터로 예측**하는 **데이터 사이언스 기반 주식 추천 플랫폼**입니다.

---

## 🚀 Service Overview

### 기획 배경
정보 과부하 시대에 개인 투자자가 **뉴스와 주가 간의 객관적 상관관계**를 파악하기 어려운 문제를 해결하고자 시작되었습니다.

### 핵심 가치
- **Data-Driven**: 직관이 아닌 데이터로 판단  
- **Efficiency**: 자동화된 탐색으로 시간 절감  
- **Back-testing**: 검증 가능한 근거 기반 전략

### 차별점
기존 플랫폼이 “현재 상황의 이유”를 설명하는 데 집중한다면, BackLoop는 **과거 사례 유사도 분석을 통해 통계적 근거를 제시**합니다.

---

## 🛠 Tech Stack

### Backend & Data Pipeline
- **Framework**: Python, Django REST Framework (DRF)  
- **Orchestration**: Apache Airflow (News ETL & Market Data Update)  
- **Database**: PostgreSQL + **pgvector** (Vector Similarity Search)  
- **In-memory DB**: Redis  
- **Infrastructure**: Docker, AWS  

### Frontend & Visualization
- **Framework**: Vue.js 3  
- **Visualization**: ApexCharts (Stock & Correlation Charts)

---

## 🧠 AI Insight Engine

BackLoop의 핵심은 **뉴스의 맥락을 데이터로 전환**하여 시장의 흐름을 읽는 것입니다.

- **NLP Embedding (Data Encoding)**  
  자연어 처리 모델을 통해 비정형 뉴스 데이터를 **고차원 벡터로 변환**합니다.
- **Semantic Search (pgvector)**  
  수만 건의 데이터 중 현재와 가장 유사한 과거 사례를 **Cosine Similarity**로 **밀리초 단위 추출**합니다.
- **Correlation Mapping**  
  추출된 과거 뉴스의 발생 시점 주가 데이터를 시각화하여 **이슈의 실질적 영향력**을 분석합니다.
- **RAG Pipeline**  
  검색 증강 생성(RAG) 기술을 통해 과거 사례를 종합한 **지능형 투자 리포트**를 생성합니다.

---

## ✨ Key Features

- **AI 뉴스 인사이트**  
  현재 뉴스와 유사도가 높은 과거 사례를 매칭하고 **Impact Score**를 산출합니다.
- **리스크 프리 모의투자**  
  실시간 KOSPI/KOSDAQ 시세를 반영한 환경에서 투자 전략을 검증합니다.
- **인사이트 쉐어링 커뮤니티**  
  데이터 기반 객관적 리포트를 공유하고 고수들의 포트폴리오를 벤치마킹합니다.
- **스마트 포트폴리오**  
  개인화된 대시보드에서 수익률 추이와 투자 성과를 시각적으로 관리합니다.

---

## 🏗 System Architecture

본 프로젝트는 데이터 수집부터 시각화까지 **유기적인 레이어 구조**로 구성되어 있습니다.

1. **Ingestion Layer**  
   Financial News Crawlers & Market Price APIs → **Apache Airflow**
2. **Processing Layer**  
   NLP Embedding Pipeline → **Correlation Engine**
3. **Storage Layer**  
   PostgreSQL (**Relational & Vector Data**)
4. **Serving Layer**  
   Django REST API → **Redis** → Vue.js Frontend

---

## 📈 Expected Benefits

| 항목 | 기존 투자 방식 | BackLoop 활용 후 |
|---|---|---|
| 투자 근거 | 주관적 직관 및 커뮤니티 의존 | 데이터 기반 객관적 상관관계 증명 |
| 정보 탐색 | 수동 차트 대조 및 검색 | AI 기반 유사 사례 자동 매핑 |
| 전략 검증 | 막연한 기대감 기반 | 과거 사례 유사도 백테스팅 |
| 의사결정 | 정보 과부하로 인한 지연 | RAG 인사이트 기반 신속 대응 |

---

## 👥 Contributors

- **원정인 (Won Jung-in)**: AI 파이프라인 설계 및 백엔드 개발  
- **윤태양 (Yoon Tae-yang)**: 데이터 아키텍처 및 프론트엔드 시각화  

**TEAM. 개미투자연구소**
