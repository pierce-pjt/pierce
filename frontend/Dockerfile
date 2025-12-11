FROM node:lts-alpine

WORKDIR /app

# 패키지 파일 복사 및 설치
COPY package*.json ./
RUN npm install

# 소스 복사
COPY . .

# 외부 접속 허용하며 실행
CMD ["npm", "run", "dev", "--", "--host"]