# 📅 연차 승인 자동 알림 봇 (Leave Auto Checker)

외주 개발사 웹사이트(연차 관리 시스템)를 10분마다 모니터링하여, **AD Data Intelligence** 부서의 새로운 연차 승인 내역이 발생할 때마다 Microsoft Teams 채널로 자동 알림을 발송하는 RPA 봇입니다. 
서버 없이 **GitHub Actions**를 통해 24시간 무료로 구동됩니다.

## 📝 시스템 파이프라인
1. **GitHub Actions:** 10분 단위(Cron)로 파이썬 스크립트 구동
2. **Playwright (Python):** Headless 브라우저로 웹사이트 자동 로그인 및 데이터 수집
3. **Data Check:** 수집된 데이터를 `leave_state.json`과 비교하여 신규 승인 건 추출
4. **Teams Webhook:** 신규 내역을 Adaptive Card 규격으로 Teams에 메시지 전송
5. **State Update:** 변경된 `leave_state.json`을 GitHub 저장소에 자동 Commit 처리

---

## 📁 주요 파일 설명

| 파일명 | 역할 | 비고 |
| :--- | :--- | :--- |
| `code_v2.py` | 메인 크롤링 및 알림 발송 스크립트 | 웹 구조 변경 시 선택자(Selector) 수정 필요 |
| `leave_state.json` | 이전에 확인한 연차 승인 내역 DB | 자동 생성 및 업데이트됨 |
| `.github/workflows/main.yml` | GitHub Actions 자동화 스케줄러 명령서 | 10분 주기 스케줄 및 봇 권한 정의 |

---

## ⚙️ 1. Teams 웹훅(Workflows) 재설정 방법
알림을 받는 방이 바뀌거나 웹훅이 끊어졌을 때 새로 발급받는 방법입니다.

1. Teams 채널 우측 상단 `...` 클릭 ➔ **워크플로(Workflows)** 선택
2. 검색창에 "웹훅" 검색 ➔ **채널에 웹후크 알림 보내기** 템플릿 선택
3. 알림을 받을 팀과 채널을 지정하고 워크플로 추가
4. 생성된 긴 URL 복사 (이후 GitHub Secrets에 등록)

---

## 🔐 2. GitHub Secrets 설정 (웹훅 주소 숨기기)
코드 보안을 위해 웹훅 URL은 절대 코드에 직접 입력하지 않고 환경 변수로 관리합니다.

1. GitHub 저장소 상단 **Settings** ➔ 좌측 **Secrets and variables** ➔ **Actions** 클릭
2. **New repository secret** 버튼 클릭
3. Name: `TEAMS_WEBHOOK_URL` 입력
4. Secret: Teams에서 복사한 웹훅 URL 전체 입력 후 저장

---

## 🚀 3. 파이썬 코드(`code_v2.py`) 체크포인트
로컬(개인 PC)에서 테스트할 때와 GitHub 서버에서 구동할 때의 설정이 다릅니다. GitHub에 코드를 올릴 때는 반드시 아래 설정을 확인하세요.

* **Headless 모드:** 모니터가 없는 서버 환경이므로 반드시 `True`여야 합니다.
  * `browser = p.chromium.launch(headless=True)`
* **환경 변수 호출:** 웹훅 주소는 하드코딩하지 않고 OS 변수를 불러옵니다.
  * `TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")`

---

## ⏰ 4. GitHub Actions 스케줄러 (`main.yml`)
`.github/workflows/main.yml` 경로에 아래 코드가 저장되어 있어야 합니다.

```yaml
name: Leave Auto Checker

on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
    - name: 저장소 가져오기
      uses: actions/checkout@v4

    - name: 파이썬 설정
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: 라이브러리 및 브라우저 설치
      run: |
        python -m pip install --upgrade pip
        pip install requests playwright
        playwright install --with-deps chromium

    - name: 파이썬 스크립트 실행
      env

```



🛠️ 트러블슈팅 및 유지보수 가이드
Q. 봇이 갑자기 멈췄거나 알림이 오지 않습니다.

웹페이지 구조 변경 의심: 웹사이트 관리자가 로그인 창이나 표(Table) 구조를 바꿨을 수 있습니다. 크롬 개발자 도구(F12)를 열고 code_v2.py에 작성된 선택자(예: input[name='name'])가 여전히 유효한지 확인하세요.

GitHub Actions 중단: 저장소에 60일 이상 커밋(변경)이 없으면 GitHub 정책상 Cron 스케줄러가 일시 중지될 수 있습니다. Actions 탭에 들어가서 'Enable workflow' 버튼을 눌러주면 다시 작동합니다.

Q. 알림이 중복해서 옵니다.

leave_state.json 파일이 제대로 Commit(저장)되지 않았을 수 있습니다. GitHub Actions의 실행 로그를 열어 마지막 단계인 "상태 파일 업데이트" 단계에서 에러가 났는지 확인하세요.

Q. 수동으로 알림 테스트를 해보고 싶습니다.

저장소의 Actions 탭 ➔ 좌측 Leave Auto Checker 클릭 ➔ 우측 Run workflow 버튼을 누르면 10분을 기다리지 않고 즉시 봇을 실행할 수 있습니다. (테스트 1건 발송용이 아닌, 실제 스크립트 전체 구동입니다.)
