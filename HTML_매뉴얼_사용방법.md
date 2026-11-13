# CEREBRO AI HTML 매뉴얼

`CEREBRO_AI_MANUAL_v0.3.md`를 참고 저장소와 같은 MkDocs Material 기반의 HTML로 변환한 배포본입니다. 원본 Markdown과 GIF는 그대로 유지합니다.

## 파일 구성

```text
CEREBRO_AI_MANUAL.html       # 매뉴얼 본문
index.html                   # 매뉴얼 시작 페이지
404.html
assets/                      # MkDocs 테마 CSS·JavaScript·검색 실행 파일
stylesheets/extra.css        # 본문·목차·인쇄 스타일
javascripts/extra.js         # 상단 제목·HOME 링크
images/logo.png              # 로컬 로고
search/search_index.json     # 로컬 검색 색인
Source/CEREBRO AI/           # 매뉴얼에서 참조하는 PNG·GIF·PDF
mkdocs.manual.yml            # HTML 생성 설정
manual-build.json            # 생성 결과·파일 연결 검증 기록
tools/build_manual_html.py   # 재생성 명령
tools/requirements-manual-html.txt
```

HTML과 위 폴더들의 상대적인 위치를 유지해 복사합니다. `CEREBRO_AI_MANUAL.html`만 따로 복사하면 이미지·GIF·스타일이 표시되지 않습니다.

GIF는 PNG로 변환하지 않았습니다. `Source/CEREBRO AI` 안의 GIF를 보관해야 움직이는 예시가 재생됩니다. 큰 이미지와 GIF는 해당 위치로 스크롤할 때 불러오도록 설정했습니다.

목차는 화면 오른쪽 끝에 기본 폭(12.1rem)으로 배치하고 글씨 크기를 줄였습니다. 본문과 목차 사이에는 구분선과 여백을 두고, 본문은 최대 1,120px 폭으로 화면 가운데에 배치합니다. 좁은 화면에서는 목차를 메뉴 안에서 확인합니다.

GIF는 원본 파일을 유지하면서 기본 표시 크기 대비 가로·세로 90%로 표시합니다. `stylesheets/extra.css`에서 `--manual-gif-scale`로 GIF 배율, `--manual-layout-width`로 본문 최대 폭, `--manual-toc-width`로 목차 폭, `--manual-toc-gap`으로 본문과 목차의 최소 간격을 조절할 수 있습니다.

## 브라우저에서 확인

프로젝트 폴더에서 다음 명령을 실행합니다.

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

브라우저에서 `http://127.0.0.1:8000/CEREBRO_AI_MANUAL.html`을 엽니다. HTML을 더블 클릭해서 본문을 볼 수도 있지만, 목차·검색 등 전체 기능은 HTTP 서버에서 확인합니다.

내부망 웹 서버에 배포할 때도 같은 폴더 구조를 사용합니다. 화면의 글꼴은 운영체제에 설치된 글꼴을 사용하며, 외부 글꼴이나 CDN 파일을 불러오지 않습니다.

## Markdown 수정 후 재생성

최초 한 번 생성 도구를 설치합니다.

```bash
python3 -m pip install -r tools/requirements-manual-html.txt
```

Markdown 내용을 수정한 후 다음 명령을 실행합니다.

```bash
python3 tools/build_manual_html.py
```

원본 MD와 사진 버전 MD는 수정하지 않고, HTML·테마 파일·검색 색인을 갱신합니다. 생성된 HTML을 직접 고치기보다 MD 또는 `stylesheets/extra.css`, `javascripts/extra.js`를 수정한 뒤 다시 생성합니다.

별도의 배포 폴더가 필요하면 다음 명령을 사용합니다.

```bash
python3 tools/build_manual_html.py --output /tmp/cerebro-manual-release
```

지정한 폴더에 HTML, 정적 파일, 본문에서 실제로 사용하는 `Source` 파일을 함께 복사합니다. 생성 시 누락된 이미지·GIF, 깨진 목차 링크, 외부 리소스 참조를 점검합니다.

## 참고

테마 버전과 폴더 구성은 [Cerebro_manual 저장소](https://github.com/dataworld9114-cerebro/Cerebro_manual)를 참고했습니다. `stylesheets/extra.css`의 기본 스타일과 `images/logo.png`도 해당 저장소의 파일을 사용하고, 이 매뉴얼에 맞는 로컬 글꼴·반응형·인쇄 설정을 추가했습니다.
