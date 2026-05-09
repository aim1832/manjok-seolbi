# 만족설비 — 정적 SEO 사이트

김해·창원 배관설비 전문업체 만족설비의 SEO 최적화 정적 사이트입니다.

## 폴더 구조
```
manjok-seolbi/
├── data/
│   ├── config.json         ← 사업체 정보, 지역, 서비스 (여기만 수정하면 사이트 전체 갱신)
│   └── posts/              ← 작업 후기 JSON 파일들 (새 후기는 여기 추가)
├── scripts/
│   └── build.py            ← 페이지 자동 생성 스크립트
├── assets/
│   ├── css/style.css       ← 사이트 디자인
│   └── img/                ← 이미지 보관
├── dist/                   ← 빌드 결과물 (자동 생성됨, 건드리지 마세요)
└── netlify.toml            ← Netlify 자동 배포 설정
```

## 새 후기 추가하는 법 (사장님이 직접 하실 작업)
1. `data/posts/` 폴더에 새 JSON 파일 만들기
   - 파일명 규칙: `YYYY-MM-DD-제목.json` (예: `2026-05-15-changwon-toilet.json`)
2. 기존 파일을 복사해서 내용 수정
3. GitHub에 push → Netlify가 자동으로 빌드 + 배포 (1~2분 소요)

## 로컬에서 빌드 테스트
```bash
python3 scripts/build.py
```
→ `dist/` 폴더에 사이트 전체 생성됨

## Netlify 자동 배포
GitHub 저장소를 Netlify와 연결하면, 코드를 push할 때마다 자동으로 사이트가 갱신됩니다.

빌드 명령어: `python3 scripts/build.py`
배포 폴더: `dist`
