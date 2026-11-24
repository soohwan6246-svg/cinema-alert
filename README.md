# 🎬 어벤져스: 둠스데이 예매 오픈 알람 (GitHub Actions 24시간 클라우드 버전)

내 PC를 꺼놔도 **GitHub 클라우드 서버**가 10분마다 메가박스·롯데시네마를 감시해, 《어벤져스: 둠스데이》 예매가 열리면 **디스코드(또는 텔레그램)**로 휴대폰 알림을 보냅니다.

---

## 🚀 3분 설정 방법 (git 설치 불필요, 웹에서 바로 업로드)

### 1단계: GitHub 새 저장소(Repository) 만들기
1. [https://github.com](https://github.com) 로그인 (계정 없으면 무료 가입)
2. 오른쪽 위 **`+` → `New repository`** 클릭
3. Repository name: `cinema-alert` 입력
4. **Public** 선택 *(중요: Public 저장소는 Actions 실행 시간이 완전 무제한 무료입니다! 디스코드 주소는 비밀금고 Secrets에 들어가므로 남에게 절대 안 보입니다.)*
5. **`Create repository`** 클릭

### 2단계: 파일 올리기
1. 만든 저장소 화면에서 **`uploading an existing file`** 링크 클릭
2. 탐색기에서 [C:\Users\taker\viewer\cinema-alert-github](file:///C:/Users/taker/viewer/cinema-alert-github) 폴더를 열고,
   **숨김 폴더(`.github`)를 포함해 안의 모든 파일(`check_cinema.py`, `notified_state.json`, `.github` 폴더, `README.md`)** 을 브라우저 창으로 드래그해서 놓기
   *(참고: 탐색기에서 `.github` 폴더가 안 보이면 탐색기 상단 `보기 → 표시 → 숨긴 항목`을 켜세요!)*
3. 아래 **`Commit changes`** 버튼 클릭

### 3단계: 디스코드 웹훅 주소 비밀금고(Secrets)에 등록
1. 저장소 상단 **`Settings`** 탭 클릭
2. 왼쪽 메뉴 **`Secrets and variables` → `Actions`** 클릭
3. **`New repository secret`** 클릭
4. Name: `DISCORD_WEBHOOK_URL`
   Secret: 아까 복사한 **디스코드 웹훅 URL** 붙여넣기 → **`Add secret`** 클릭

### 4단계: 테스트 실행 & 작동 확인
1. 저장소 상단 **`Actions`** 탭 클릭
2. 왼쪽에서 **`Cinema Ticket Alert (Avengers Doomsday)`** 클릭
3. 오른쪽 **`Run workflow` → 초록색 `Run workflow`** 클릭!
4. 10초 뒤 폰 디스코드 앱으로 **테스트 알림**이 오면 세팅 완료! 이제 PC를 끄셔도 24시간 자동 감시됩니다.

---

### ⚙️ 지점/영화 바꾸고 싶을 때
GitHub 웹에서 `check_cinema.py` 파일을 눌러 연필(✏️) 아이콘을 누르면 바로 수정 가능합니다:
* `KEYWORDS = ["둠스데이", "doomsday"]`
* `LOTTE_BRANCH_NAME = "월드타워"`
* `MEGABOX_BRANCH_NAME = "코엑스"`
* `SCREEN_FILTERS = []` *(예: `["돌비", "수퍼플렉스"]` 입력 시 해당 관만 알림)*
