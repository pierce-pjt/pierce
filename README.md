# 🚀 Pierce 프로젝트

이 프로젝트는 Airflow, Django, Postgres(pgvector)를 Docker Compose로 실행합니다.

## ⚙️ 사전 요구 사항

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
* [Git](https://git-scm.com/) 설치

## 🏁 로컬 환경 세팅 (최초 1회)

1.  **Git 저장소 클론**
    ```bash
    git clone [이 저장소 주소]
    cd pierce_pjt
    ```

2.  **비밀번호 파일 생성**
    `.env.example` 파일을 복사하여 `.env` 파일을 만듭니다.
    ```bash
    cp .env.example .env
    ```
    그런 다음, `.env` 파일을 열어 Slack 등으로 전달받은 실제 DB 정보를 입력합니다.

3.  **Docker 컨테이너 빌드 및 실행**
    ```bash
    docker compose up --build
    ```
    (최초 실행 시 빌드 때문에 몇 분 정도 소요될 수 있습니다.)

4.  **Django 마이그레이션 (DB 테이블 생성)**
    위의 터미널은 그대로 둔 채로, **새로운 터미널**을 열어서 다음을 실행합니다.
    ```bash
    docker compose exec django python manage.py migrate
    ```

5.  **(선택) Django 슈퍼유저 생성**
    같은 새 터미널에서 다음을 실행하고, ID와 PW를 입력합니다.
    ```bash
    docker compose exec django python manage.py createsuperuser
    ```

## 🖥️ 서비스 접속

모든 컨테이너가 성공적으로 실행되면, 다음 주소로 접속할 수 있습니다.

* **Airflow 대시보드:** [http://localhost:8080](http://localhost:8080)
* **Django 개발 서버:** [http://localhost:8000](http://localhost:8000)
* **Django 어드민:** [http://localhost:8000/admin](http://localhost:8000/admin)

## 🛑 중지

프로젝트를 중지하려면 로그가 올라오는 터미널에서 `Ctrl + C`를 누르거나, 새 터미널에서 다음을 실행합니다.

```bash
docker compose down
