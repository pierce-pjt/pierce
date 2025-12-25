### 기획 배경
정보 과부하 시대에 개인 투자자가 **뉴스와 주가 간의 객관적 상관관계**를 파악하기 어려운 문제를 해결하고자 시작되었습니다.

# 📊 Pierce - AI 기반 주식 투자 플랫폼

> **뉴스 기반 종목 추천부터 모의 투자, 커뮤니티까지 - 올인원 주식 투자 학습 플랫폼**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0+-4FC08D.svg)](https://vuejs.org/)
[![Airflow](https://img.shields.io/badge/Airflow-2.8+-017CEE.svg)](https://airflow.apache.org/)

###
![아키텍쳐](./image/architecture.png)

## 🎯 프로젝트 개요

Pierce는 **AI 기반 뉴스 분석**과 **RAG(Retrieval-Augmented Generation)** 기술을 활용하여 개인 투자자들에게 데이터 기반의 투자 인사이트를 제공하는 종합 주식 투자 플랫폼입니다.

### 핵심 기능

- 🤖 **AI 뉴스 분석 기반 종목 추천**: 실시간 뉴스 데이터를 RAG로 분석하여 투자 아이디어 제공
- 📈 **실시간 주가 차트**: 기술적 지표(이동평균선, 볼린저밴드 등)와 함께 제공되는 인터랙티브 차트
- 💰 **모의 투자 시스템**: 가상 자금으로 안전하게 투자 전략 테스트
- 👥 **투자 커뮤니티**: 다른 투자자들과 전략 공유 및 소셜 트레이딩
- 📊 **포트폴리오 분석**: 실시간 수익률 추적 및 거래 내역 관리
- 🔔 **관심 종목 관리**: 워치리스트 기능으로 종목 모니터링

## 🏗️ 기술 스택

### Backend
- **Django 5.0+** - RESTful API 서버
- **Django REST Framework** - API 개발 프레임워크
- **PostgreSQL + pgvector** - 벡터 검색을 위한 확장 DB
- **Apache Airflow** - 데이터 파이프라인 및 스케줄링
- **Docker & Docker Compose** - 컨테이너화 및 오케스트레이션
- **Redis**: 인 메모리 DB  

### Frontend
- **Vue.js 3** - 프론트엔드 프레임워크
- **Vuetify 3** - Material Design 컴포넌트 라이브러리
- **Pinia** - 상태 관리
- **Chart.js / Lightweight Charts** - 주가 차트 시각화
- **Axios** - HTTP 클라이언트

### AI & Data
- **OpenAI API** - LLM 기반 뉴스 분석 및 추천
- **RAG (Retrieval-Augmented Generation)** - 벡터 검색 기반 문맥 인식 AI
- **한국투자증권 API** - 실시간 주가 데이터 수집
- **Beautiful Soup / Selenium** - 뉴스 크롤링

### Infrastructure
- **Docker** - 컨테이너 기반 배포
- **Nginx** (예정) - 리버스 프록시 및 정적 파일 서빙
- **GitHub Actions** (예정) - CI/CD 파이프라인

## 📁 프로젝트 구조

```
pierce/
├── django_app/              # Django 백엔드 애플리케이션
│   ├── accounts/           # 사용자 인증 및 관리
│   ├── stocks/             # 주식 데이터 및 거래 로직
│   ├── community/          # 커뮤니티 게시판
│   ├── news/               # 뉴스 관리 및 분석
│   └── api/                # RESTful API 엔드포인트
│
├── frontend/               # Vue.js 프론트엔드
│   ├── src/
│   │   ├── components/    # 재사용 가능한 컴포넌트
│   │   ├── views/         # 페이지 뷰
│   │   ├── stores/        # Pinia 스토어
│   │   ├── router/        # Vue Router 설정
│   │   └── api/           # API 클라이언트
│   └── public/
│
├── dags/                   # Airflow DAG 정의
│   ├── stock_data_pipeline.py    # 주가 데이터 수집 파이프라인
│   └── news_analysis_pipeline.py # 뉴스 분석 파이프라인
│
├── scripts/                # 유틸리티 스크립트
├── init/                   # 초기 설정 스크립트
├── docker-compose.yml      # Docker Compose 설정
├── Dockerfile.airflow      # Airflow 커스텀 이미지
└── requirements_airflow.txt # Python 의존성
```

## 🚀 시작하기

### 사전 요구사항

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- [Git](https://git-scm.com/) 설치
- 최소 8GB RAM (권장: 16GB)
- 한국투자증권 API 키 (선택사항)

### 설치 및 실행

1. **저장소 클론**
   ```bash
   git clone https://github.com/pierce-pjt/pierce.git
   cd pierce
   ```

2. **환경 변수 설정**
   ```bash
   cp .env.example .env
   ```
   
   `.env` 파일을 열어 다음 정보를 입력:
   ```env
   # Database
   POSTGRES_DB=pierce_db
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   
   # Django
   DJANGO_SECRET_KEY=your_secret_key
   
   # API Keys
   KIS_APP_KEY=your_korea_investment_api_key
   KIS_APP_SECRET=your_korea_investment_secret
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **Docker 컨테이너 빌드 및 실행**
   ```bash
   docker-compose up --build -d
   ```
   
   최초 실행 시 이미지 빌드로 5-10분 소요될 수 있습니다.

4. **Django 마이그레이션 실행**
   ```bash
   docker-compose exec django python manage.py migrate
   ```

5. **슈퍼유저 생성 (선택사항)**
   ```bash
   docker-compose exec django python manage.py createsuperuser
   ```

6. **초기 데이터 로드 (선택사항)**
   ```bash
   docker-compose exec django python manage.py loaddata initial_stocks.json
   ```

### 서비스 접속

모든 서비스가 정상적으로 실행되면:

- **🌐 프론트엔드**: [http://localhost:3000](http://localhost:3000)
- **🔧 Django Admin**: [http://localhost:8000/admin](http://localhost:8000/admin)
- **📡 Django API**: [http://localhost:8000/api](http://localhost:8000/api)
- **🔄 Airflow UI**: [http://localhost:8080](http://localhost:8080)
  - Username: `admin`
  - Password: `admin` (변경 권장)


## 🎨 주요 화면

### 1. 대시보드
- 실시간 시장 현황 및 주요 지수
- 포트폴리오 요약 (총 자산, 수익률)
- AI 추천 종목 및 핫 뉴스

### 2. 종목 상세
- 실시간 주가 차트 (캔들스틱, 라인)
- 기술적 지표 (MA5, MA20, MA60, 볼린저밴드)
- 호가창 및 체결 내역
- AI 기반 뉴스 요약 및 감성 분석

### 3. 모의 투자
- 매수/매도 주문 시스템
- 실시간 포트폴리오 추적
- 거래 내역 및 손익 분석

### 4. 커뮤니티
- 투자 아이디어 공유 게시판
- 종목별 토론방
- 팔로우/팔로잉 시스템
- 좋아요 및 댓글 기능

### 5. 마이페이지
- 포트폴리오 현황
- 보유 종목 및 수익률
- 거래 내역
- 투자 전략 메모
- 관심 종목 관리


### API 테스트

Django REST Framework의 Browsable API 활용:
```
http://localhost:8000/api/
```

주요 엔드포인트:
- `GET /api/stocks/` - 종목 리스트
- `GET /api/stocks/{ticker}/` - 종목 상세
- `POST /api/transactions/` - 거래 주문
- `GET /api/portfolio/` - 포트폴리오 조회
- `GET /api/posts/` - 커뮤니티 게시글

### 데이터 파이프라인

Airflow DAG 관리:
1. Airflow UI 접속: `http://localhost:8080`
2. DAGs 탭에서 파이프라인 활성화
3. 수동 실행 또는 스케줄 설정

주요 DAG:
- `stock_data_collection` - 매일 주가 데이터 수집
- `news_scraping_analysis` - 매시간 뉴스 크롤링 및 분석
- `portfolio_update` - 포트폴리오 평가액 업데이트

## 🤝 기여하기

프로젝트 개선을 위한 기여를 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 코딩 컨벤션
- Python: PEP 8 준수
- JavaScript/Vue: ESLint + Prettier 설정 적용
- Commit Message: [Conventional Commits](https://www.conventionalcommits.org/) 사용


## 👥 팀원

- **[JeonginWon](https://github.com/JeonginWon)** - Backend & AI & Frontend & Data & Design
- **[youn-sun](https://github.com/youn-sun)** - AI & & Data & Backend & Frontend & System

---

<p align="center">
  Made with ❤️ by Pierce Team
</p>