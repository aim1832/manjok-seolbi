"""
==========================================================
만족설비 — 정적 SEO 페이지 자동 생성기
==========================================================
역할:
  1) data/config.json (지역 + 서비스 정보) 읽기
  2) 메인 페이지(index.html) 생성
  3) 지역×서비스 조합별 페이지 자동 생성 (예: /jangyu1-drain-clog/)
  4) 작업 후기 페이지 생성 (data/posts/*.json 기반)
  5) sitemap.xml, robots.txt 자동 생성
  6) 모든 페이지에 SEO 메타태그 + JSON-LD 구조화 데이터 삽입

사용법:
  python scripts/build.py

실행 후 dist/ 폴더 안에 사이트 전체가 생성됨 → 그대로 GitHub에 push
==========================================================
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# Pillow는 이미지 자동 압축용 (없으면 압축 없이 진행)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow 미설치 — 이미지 압축 없이 진행 (pip install Pillow 권장)")

# ===== 이미지 자동 압축 설정 =====
IMG_MAX_WIDTH = 1600        # 최대 가로 픽셀 (이보다 크면 자동으로 줄임)
IMG_QUALITY = 82            # JPEG 품질 (0~100, 80~85가 균형 좋음)
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# ===== 경로 설정 =====
ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "config.json"
POSTS_DIR = ROOT / "data" / "posts"
DIST_DIR = ROOT / "dist"
ASSETS_SRC = ROOT / "assets"

# ===== 설정 로드 =====
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

BIZ = CONFIG["business"]
SERVICES = CONFIG["services"]
REGIONS = CONFIG["regions"]
SITE_URL = CONFIG["site"]["url"]


# ============================================================
# 공통 HTML 컴포넌트
# ============================================================
def head_html(title, description, canonical_path, og_image=None):
    """모든 페이지에 들어가는 <head> 영역 — SEO의 핵심"""
    canonical = f"{SITE_URL}{canonical_path}"
    og_image = og_image or f"{SITE_URL}{CONFIG['site']['default_og_image']}"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="keywords" content="김해 배관, 창원 배관, 김해 하수구막힘, 창원 하수구막힘, 김해 변기수리, 창원 변기수리, 김해 수전교체, 만족설비">
<meta name="author" content="{BIZ['name']}">
<meta name="robots" content="index, follow">

<!-- Open Graph (네이버/카카오톡 공유 시) -->
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="{BIZ['name']}">

<!-- 검색엔진 사이트확인 (네이버/구글 등록 시 채워넣음) -->
<meta name="naver-site-verification" content="8edd49471f1891161914188e9e2ebba9e81503f0">
<meta name="google-site-verification" content="">

<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="/assets/css/style.css">

<!-- JSON-LD 지역업체 구조화 데이터 -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "{BIZ['name']}",
  "image": "{og_image}",
  "telephone": "{BIZ['phone']}",
  "url": "{SITE_URL}",
  "description": "{BIZ['description']}",
  "areaServed": ["김해", "창원"],
  "openingHours": "Mo-Su 00:00-23:59",
  "priceRange": "₩₩"
}}
</script>
</head>
<body>
"""


def header_html():
    return f"""
<div class="top-bar">
  📞 24시간 출장 상담 — <a href="tel:{BIZ['phone_tel']}" style="color:#fff;text-decoration:underline;">{BIZ['phone_display']}</a>
  &nbsp;|&nbsp;
  <a href="{BIZ['kakao_url']}" target="_blank" style="color:#fff;text-decoration:underline;">💬 카톡 상담</a>
</div>
<header class="header">
  <div class="header-inner">
    <a href="/" class="logo">만족설비</a>
    <div class="header-actions">
      <a href="{BIZ['kakao_url']}" target="_blank" class="header-kakao">💬 카톡상담</a>
      <a href="tel:{BIZ['phone_tel']}" class="header-phone">📞 {BIZ['phone_display']}</a>
    </div>
  </div>
</header>
"""


def floating_call_html():
    return f"""
<div class="floating-buttons">
  <a href="{BIZ['kakao_url']}" target="_blank" class="floating-kakao">
    <span class="floating-icon">💬</span>
    <span class="floating-text">카톡상담</span>
  </a>
  <a href="tel:{BIZ['phone_tel']}" class="floating-call">
    <span class="floating-icon">📞</span>
    <span class="floating-text">즉시통화</span>
  </a>
</div>
"""


def footer_html():
    return f"""
<footer class="footer">
  <div class="footer-info">
    <strong>{BIZ['name']}</strong>
    <p>김해·창원 전지역 배관설비 출장 서비스</p>
    <p>📞 {BIZ['phone_display']} (연중무휴 24시간 상담)</p>
  </div>
  <div class="footer-bottom">
    © {datetime.now().year} {BIZ['name']}. All rights reserved.
  </div>
</footer>
{floating_call_html()}
</body>
</html>
"""


def cta_box_html(text="작업 상담은 전화 한 통이면 끝!"):
    return f"""
<div class="cta-box">
  <h3>지금 막힘·누수로 곤란하신가요?</h3>
  <p>{text} 김해·창원 전지역 빠른 출장 가능합니다.</p>
  <div class="cta-buttons">
    <a href="tel:{BIZ['phone_tel']}" class="btn btn-cta-call">📞 {BIZ['phone_display']}</a>
    <a href="{BIZ['kakao_url']}" target="_blank" class="btn btn-cta-kakao">💬 카톡으로 상담받기</a>
  </div>
  <p class="cta-tip">💡 카톡으로 작업 부위 사진 보내주시면 정확한 견적을 빠르게 안내드립니다!</p>
</div>
"""


def service_icon_svg(slug):
    """서비스별 커스텀 SVG 아이콘"""
    primary = "#2d4a2b"
    accent = "#8b6f47"

    if slug == "drain-clog":
        # 하수구 막힘 — P트랩 배관
        return f'''<svg width="48" height="48" viewBox="0 0 32 32" fill="none" stroke="{primary}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M3 10 L13 10 L13 20 L19 20 L19 10 L29 10" />
  <rect x="2" y="8" width="3" height="4" fill="{primary}" stroke="none"/>
  <rect x="27" y="8" width="3" height="4" fill="{primary}" stroke="none"/>
  <rect x="11" y="18" width="2" height="4" fill="{primary}" stroke="none"/>
  <rect x="19" y="8" width="2" height="4" fill="{primary}" stroke="none"/>
</svg>'''

    if slug == "faucet-replace":
        # 수전 교체 — Tabler tool 아이콘 흉내
        return f'''<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M7 10h3v-3l-3.5 -3.5a6 6 0 0 1 8 8l6 6a2 2 0 0 1 -3 3l-6 -6a6 6 0 0 1 -8 -8l3.5 3.5"/>
</svg>'''

    if slug == "toilet-service":
        # 변기 교체 및 수리
        return f'''<svg width="48" height="48" viewBox="0 0 32 32" fill="none" stroke="{primary}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M9 5 L23 5 L23 12 L9 12 Z" />
  <path d="M11 12 L11 17" />
  <path d="M21 12 L21 17" />
  <ellipse cx="16" cy="20" rx="9" ry="4" />
  <path d="M9 22 L9 26 Q9 28 11 28 L21 28 Q23 28 23 26 L23 22" />
</svg>'''

    if slug == "sink-service":
        # 세면대 교체 및 수리
        return f'''<svg width="48" height="48" viewBox="0 0 32 32" fill="none" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M16 4 L16 8" />
  <path d="M14 8 L18 8 L18 11 L14 11 Z" fill="{accent}" stroke="{accent}"/>
  <path d="M16 11 L16 15" />
  <path d="M5 16 L27 16 L25 22 Q25 24 23 24 L9 24 Q7 24 7 22 Z" />
  <line x1="14" y1="20" x2="18" y2="20" stroke-width="2"/>
  <path d="M14 24 L14 27" />
  <path d="M18 24 L18 27" />
</svg>'''

    if slug == "bathtub-drain":
        # 욕조 배수구 교체
        return f'''<svg width="48" height="48" viewBox="0 0 32 32" fill="none" stroke="{primary}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path d="M4 12 L4 14 L4 20 Q4 24 8 24 L24 24 Q28 24 28 20 L28 14 L28 12 Z" />
  <path d="M4 16 L28 16" />
  <circle cx="9" cy="20" r="1.5" fill="{primary}" stroke="none"/>
  <path d="M14 8 Q14 6 16 6 Q18 6 18 8 L18 11" />
  <line x1="14" y1="11" x2="20" y2="11" stroke-width="2"/>
  <path d="M22 24 L22 27" />
  <path d="M10 24 L10 27" />
</svg>'''

    # 기본 아이콘 (없는 경우)
    return f'''<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="{primary}" stroke-width="2" aria-hidden="true">
  <circle cx="12" cy="12" r="9"/>
</svg>'''


# ============================================================
# 1. 메인 페이지 생성
# ============================================================
def build_index():
    title = f"{BIZ['name']} | 김해·창원 배관설비 24시간 출장"
    desc = BIZ["description"]
    html = head_html(title, desc, "/")
    html += header_html()

    # 히어로
    html += f"""
<section class="hero">
  <div class="hero-badge">✓ 꼼꼼한 시공 · 정직한 견적</div>
  <h1>우리 동네 믿을 수 있는<br>배관 전문가</h1>
  <p class="subtitle">— {BIZ['name']} —</p>
  <div class="cta-group">
    <a href="tel:{BIZ['phone_tel']}" class="btn btn-primary">📞 {BIZ['phone_display']}</a>
    <a href="{BIZ['kakao_url']}" target="_blank" class="btn btn-kakao">💬 카톡 상담</a>
    <a href="#services" class="btn btn-secondary">서비스 보기</a>
  </div>
  <p class="hero-tip">💡 카톡으로 사진 보내주시면 빠른 견적 안내!</p>
</section>

<section class="trust-stats">
  <div class="trust-stats-inner">
    <div class="trust-item">
      <div class="trust-num">10<span>년+</span></div>
      <div class="trust-label">운영 경력</div>
    </div>
    <div class="trust-item">
      <div class="trust-num brown">5,000<span>건+</span></div>
      <div class="trust-label">누적 시공</div>
    </div>
    <div class="trust-item">
      <div class="trust-num warning">미해결시</div>
      <div class="trust-label warning">0원 보장</div>
    </div>
  </div>
</section>
"""

    # 서비스
    html += '<section id="services" class="container">'
    html += '<h2 class="section-title">주요 서비스</h2>'
    html += '<p class="section-subtitle">우리 집 같은 마음으로 시공합니다</p>'
    html += '<div class="services-grid">'
    for s in SERVICES:
        icon_svg = service_icon_svg(s['slug'])
        html += f"""
  <div class="service-card">
    <div class="service-icon">{icon_svg}</div>
    <h3>{s['name']}</h3>
    <p>{s['description']}</p>
  </div>"""
    html += "</div></section>"

    # 특장점
    html += """
<section class="features">
  <div class="container">
    <h2 class="section-title">왜 만족설비인가요?</h2>
    <div class="features-grid">
      <div class="feature-item">
        <div class="feature-num">1</div>
        <h4>당일 즉시 출동</h4>
        <p>전화 한 통이면 김해·창원 어디든 빠르게 출장 갑니다.</p>
      </div>
      <div class="feature-item">
        <div class="feature-num">2</div>
        <h4>합리적 견적</h4>
        <p>출장 전 통화로 예상 견적 안내. 추가 청구 없는 정찰제.</p>
      </div>
      <div class="feature-item">
        <div class="feature-num">3</div>
        <h4>전문 장비 보유</h4>
        <p>고압세척기·관로탐지기 등 전문 장비로 정확하게 시공.</p>
      </div>
      <div class="feature-item">
        <div class="feature-num">4</div>
        <h4>사후 A/S 보장</h4>
        <p>작업 후 문제 발생 시 빠르게 재방문해드립니다.</p>
      </div>
    </div>
  </div>
</section>
"""

    # 작업 가능 지역
    html += '<section class="regions-block container">'
    html += '<h2 class="section-title">작업 가능 지역</h2>'
    html += '<p class="section-subtitle">김해·창원 전지역, 클릭 시 해당 지역 안내 페이지로 이동합니다</p>'
    for region_key, region_data in REGIONS.items():
        html += f'<div class="region-group"><h3>{region_data["name"]}</h3><div class="region-tags">'
        for d in region_data["districts"]:
            # 첫 번째 서비스 페이지로 링크
            first_service = SERVICES[0]["slug"]
            html += f'<a href="/{d["slug"]}-{first_service}/" class="region-tag">{d["name"]}</a>'
        html += "</div></div>"
    html += "</section>"

    # 최근 후기 (있을 때만)
    posts = load_posts()
    if posts:
        html += '<section class="container" style="background:#f5f7fa;">'
        html += '<h2 class="section-title">최근 작업 후기</h2>'
        html += '<div class="reviews-grid">'
        for p in posts[:6]:
            thumb = p.get("thumbnail", "")
            html += f"""
  <a href="/post/{p['slug']}/" style="text-decoration:none;color:inherit;">
    <div class="review-card">
      <div class="thumb" style="background-image:url('{thumb}');"></div>
      <div class="body">
        <span class="badge">{p.get('service_name', '')}</span>
        <h4>{p['title']}</h4>
        <p class="meta">{p.get('region', '')} · {p.get('date', '')}</p>
      </div>
    </div>
  </a>"""
        html += "</div></section>"

    # CTA
    html += '<div class="container">'
    html += cta_box_html()
    html += "</div>"

    html += footer_html()
    write_file(DIST_DIR / "index.html", html)


# ============================================================
# 2. 지역×서비스 페이지 자동 생성 (SEO 핵심!)
# ============================================================
# ============================================================
# ⭐ 자동 연결 시스템 — 후기와 지역×서비스 페이지를 자동 연결
# ============================================================

# 인근 지역 매핑 (장유 근처는 같은 생활권으로 묶음)
NEARBY_REGIONS = {
    # 장유 생활권 (서부)
    "jangyu": ["jangyu-dong", "yulha", "mugye", "naedeok", "daecheong", "bugok", "sammun", "suga", "yuha", "eungdal", "kwandong", "shinmun"],
    "jangyu-dong": ["jangyu", "yulha", "mugye", "naedeok", "daecheong", "bugok", "sammun", "suga", "yuha", "eungdal", "kwandong", "shinmun"],
    "yulha": ["jangyu", "jangyu-dong", "mugye", "daecheong", "bugok", "kwandong"],
    "mugye": ["jangyu", "jangyu-dong", "yulha", "naedeok", "daecheong"],
    "naedeok": ["jangyu", "jangyu-dong", "mugye", "daecheong", "bugok"],
    "daecheong": ["jangyu", "jangyu-dong", "yulha", "mugye", "naedeok"],
    "bugok": ["jangyu", "jangyu-dong", "yulha", "naedeok"],
    "sammun": ["jangyu", "jangyu-dong", "suga", "yuha"],
    "suga": ["jangyu", "jangyu-dong", "sammun", "yuha"],
    "yuha": ["jangyu", "jangyu-dong", "sammun", "suga"],
    "eungdal": ["jangyu", "jangyu-dong", "kwandong"],
    "kwandong": ["jangyu", "jangyu-dong", "yulha", "eungdal", "shinmun"],
    "shinmun": ["jangyu", "jangyu-dong", "kwandong"],

    # 김해 도심 생활권
    "naeoe": ["bukbu", "samgye", "dongsang", "seosang", "buwon"],
    "bukbu": ["naeoe", "samgye", "samjeong"],
    "samgye": ["naeoe", "bukbu", "samjeong", "sambang"],
    "dongsang": ["seosang", "buwon", "bonghwang", "daeseong", "naeoe"],
    "seosang": ["dongsang", "buwon", "bonghwang", "daeseong", "naeoe"],
    "buwon": ["dongsang", "seosang", "bonghwang", "naeoe"],
    "bonghwang": ["dongsang", "seosang", "buwon", "daeseong"],
    "daeseong": ["dongsang", "seosang", "bonghwang"],
    "saman": ["hwalcheon", "eobang", "andong"],
    "hwalcheon": ["saman", "eobang", "andong"],
    "eobang": ["hwalcheon", "saman", "andong"],
    "andong": ["hwalcheon", "saman", "eobang", "jinae"],
    "sambang": ["samgye", "samjeong"],
    "samjeong": ["bukbu", "samgye", "sambang"],
    "buram": ["chilsan-seobu", "hoehyeon"],
    "chilsan-seobu": ["buram", "hoehyeon"],
    "hoehyeon": ["buram", "chilsan-seobu", "naedong"],
    "naedong": ["hoehyeon", "oedong"],
    "oedong": ["naedong", "hoehyeon"],
    "gusan": ["naeoe", "samgye"],
    "jinae": ["andong", "saman"],

    # 김해 외곽
    "myeongbeop": ["jeonha", "hwamok"],
    "jeonha": ["myeongbeop", "hwamok", "heungdong"],
    "hwamok": ["myeongbeop", "jeonha", "heungdong"],
    "heungdong": ["jeonha", "hwamok", "pungyu"],
    "pungyu": ["heungdong"],
    "guji": ["jinyeong"],

    # 읍·면 단위
    "jinyeong": ["jinrye", "hanrim", "guji"],
    "jinrye": ["jinyeong", "hanrim"],
    "hanrim": ["jinrye", "jinyeong", "saengrim"],
    "saengrim": ["hanrim", "sangdong"],
    "sangdong": ["saengrim", "daedong"],
    "daedong": ["sangdong", "juchon"],
    "juchon": ["daedong"],
}


def build_post_index(posts):
    """후기들을 지역/서비스별로 인덱싱.

    각 후기에서 어떤 지역(district slug)과 매칭되는지 자동 추출.
    """
    index = {
        "by_district": {},  # district_slug -> [posts]
        "by_district_service": {},  # (district_slug, service_slug) -> [posts]
    }

    # 모든 동 이름 → slug 매핑 만들기
    name_to_slug = {}
    for region_key, region_data in REGIONS.items():
        for d in region_data["districts"]:
            name_to_slug[d["name"]] = d["slug"]

    for post in posts:
        region_text = post.get("region", "")
        service_slug = post.get("service_slug", "")

        # 후기의 region 텍스트에서 동 이름 추출
        matched_districts = set()
        for name, slug in name_to_slug.items():
            if name in region_text:
                matched_districts.add(slug)

        # 인덱스에 추가
        for d_slug in matched_districts:
            index["by_district"].setdefault(d_slug, []).append(post)
            key = (d_slug, service_slug)
            index["by_district_service"].setdefault(key, []).append(post)

    return index


def find_matching_posts(district, service, post_index):
    """이 페이지에 표시할 후기들을 찾기.

    반환:
      exact: 정확히 이 지역+이 서비스 후기
      same_region_other: 같은 지역의 다른 서비스 후기
      nearby: 인근 지역의 같은 서비스 후기
    """
    d_slug = district["slug"]
    s_slug = service["slug"]

    exact = post_index["by_district_service"].get((d_slug, s_slug), [])

    # 같은 지역, 다른 서비스
    same_region_all = post_index["by_district"].get(d_slug, [])
    same_region_other = [p for p in same_region_all if p.get("service_slug") != s_slug]

    # 인근 지역, 같은 서비스
    nearby = []
    nearby_slugs = NEARBY_REGIONS.get(d_slug, [])
    for nearby_slug in nearby_slugs:
        nearby_posts = post_index["by_district_service"].get((nearby_slug, s_slug), [])
        nearby.extend(nearby_posts)

    # 중복 제거 (정확 매칭에 있는 건 다른 영역에서 제외)
    exact_slugs = {p["slug"] for p in exact}
    same_region_other = [p for p in same_region_other if p["slug"] not in exact_slugs]
    nearby = [p for p in nearby if p["slug"] not in exact_slugs]

    # 최신순 정렬 + 개수 제한
    exact.sort(key=lambda p: p.get("date", ""), reverse=True)
    same_region_other.sort(key=lambda p: p.get("date", ""), reverse=True)
    nearby.sort(key=lambda p: p.get("date", ""), reverse=True)

    return {
        "exact": exact[:3],
        "same_region_other": same_region_other[:2],
        "nearby": nearby[:2],
    }


def render_exact_match_reviews(district, service, posts):
    """정확히 매칭되는 후기 영역 — 본문도 풍부하게"""
    if not posts:
        return ""

    # 사례 요약 문장 자동 생성 (보너스 기능)
    main_post = posts[0]
    summary_html = f"""
  <h2>{district['name']} 지역 {service['name']} 실제 작업 사례</h2>
  <p>만족설비는 <strong>{district['name']}</strong> 지역에서 다양한 {service['name']} 작업을 진행했습니다.
  대표적으로 <strong>{main_post.get('region', '')}</strong>에서 작업한 사례가 있으며, 합리적 비용에 신속하게 시공해드렸습니다.
  자세한 작업 과정과 사진은 아래 후기에서 확인하실 수 있어요.</p>
"""

    html = summary_html
    html += f'<div class="reviews-grid" style="margin-top:20px;">'

    for p in posts:
        thumb = p.get("thumbnail", "")
        thumb_style = f'style="background-image:url({thumb});"' if thumb else ""
        date = p.get("date", "")
        region = p.get("region", "")

        html += f"""
    <a href="/post/{p['slug']}/" class="review-card">
      <div class="thumb" {thumb_style}></div>
      <div class="body">
        <span class="badge">{service['name']}</span>
        <h4>{p['title']}</h4>
        <p class="meta">📍 {region} · {date}</p>
      </div>
    </a>"""

    html += "</div>"
    return html


def render_same_region_reviews(district, posts):
    """같은 지역의 다른 서비스 후기"""
    if not posts:
        return ""

    html = f"""
  <h2>{district['name']} 지역의 다른 작업 후기</h2>
  <p>만족설비는 <strong>{district['name']}</strong> 지역에서 다양한 배관설비 작업을 수행하고 있습니다.
  하수구 막힘, 수전 교체, 변기·세면대 수리 등 어떤 작업이든 맡겨주세요.</p>
"""
    html += f'<div class="reviews-grid" style="margin-top:20px;">'

    for p in posts:
        thumb = p.get("thumbnail", "")
        thumb_style = f'style="background-image:url({thumb});"' if thumb else ""
        date = p.get("date", "")
        region = p.get("region", "")
        service_name = p.get("service_name", "")

        html += f"""
    <a href="/post/{p['slug']}/" class="review-card">
      <div class="thumb" {thumb_style}></div>
      <div class="body">
        <span class="badge">{service_name}</span>
        <h4>{p['title']}</h4>
        <p class="meta">📍 {region} · {date}</p>
      </div>
    </a>"""

    html += "</div>"
    return html


def render_nearby_reviews(district, service, posts):
    """인근 지역의 같은 서비스 후기"""
    if not posts:
        return ""

    html = f"""
  <h2>인근 지역 {service['name']} 작업 후기</h2>
  <p><strong>{district['name']}</strong> 인근 지역에서 진행한 {service['name']} 작업 사례입니다.
  {district['name']}에서도 동일한 품질로 빠르게 출장 가능합니다.</p>
"""
    html += f'<div class="reviews-grid" style="margin-top:20px;">'

    for p in posts:
        thumb = p.get("thumbnail", "")
        thumb_style = f'style="background-image:url({thumb});"' if thumb else ""
        date = p.get("date", "")
        region = p.get("region", "")

        html += f"""
    <a href="/post/{p['slug']}/" class="review-card">
      <div class="thumb" {thumb_style}></div>
      <div class="body">
        <span class="badge">{service['name']}</span>
        <h4>{p['title']}</h4>
        <p class="meta">📍 {region} · {date}</p>
      </div>
    </a>"""

    html += "</div>"
    return html


def build_region_service_pages():
    """예: /jangyu1-drain-clog/ → 장유1동 하수구 막힘 페이지"""
    # 후기 데이터 미리 로드 + 매칭 인덱스 구축
    all_posts = load_posts()
    post_index = build_post_index(all_posts)

    count = 0
    for region_key, region_data in REGIONS.items():
        city_name = region_data["name"]
        for d in region_data["districts"]:
            for s in SERVICES:
                slug = f"{d['slug']}-{s['slug']}"
                title = f"{d['name']} {s['name']} | {city_name} 배관설비 {BIZ['name']}"
                desc = (
                    f"{city_name} {d['name']} {s['name']} 전문 시공. "
                    f"{s['description']} 24시간 출장 상담 {BIZ['phone_display']}"
                )
                html = head_html(title, desc, f"/{slug}/")
                html += header_html()

                html += f"""
<section class="post-header">
  <h1>{d['name']} {s['name']} — {BIZ['name']}</h1>
  <div class="post-meta">
    <span>📍 {city_name} {d['name']}</span>
    <span>{s['icon']} {s['name']}</span>
  </div>
</section>

<article class="post-content">
  <h2>{d['name']} 지역 {s['name']} 작업, 만족설비에 맡겨주세요</h2>
  <p>안녕하세요, 김해·창원 배관설비 전문업체 <strong>{BIZ['name']}</strong>입니다.
  {city_name} {d['name']} 일대에서 {s['name']} 작업이 필요하신 고객님께 빠르고 정확한 시공으로 보답드리고 있습니다.</p>

  <p>{s['description']}</p>
"""

                # ⭐ 자동 연결 시스템 — 매칭되는 실제 작업 후기 표시
                matched_posts = find_matching_posts(d, s, post_index)
                if matched_posts["exact"]:
                    html += render_exact_match_reviews(
                        d, s, matched_posts["exact"]
                    )
                if matched_posts["same_region_other"]:
                    html += render_same_region_reviews(
                        d, matched_posts["same_region_other"]
                    )
                if matched_posts["nearby"]:
                    html += render_nearby_reviews(
                        d, s, matched_posts["nearby"]
                    )

                html += f"""
  <h2>{d['name']} {s['name']}, 이런 경우 연락주세요</h2>
  <ul>
"""
                for kw in s["title_keywords"]:
                    html += f"    <li>{kw} 관련 문의</li>\n"
                html += f"""
    <li>{d['name']} 인근 빠른 출장이 필요하신 경우</li>
    <li>견적 비교 후 합리적인 가격을 원하시는 경우</li>
  </ul>

  <h2>작업 절차 안내</h2>
  <ol>
    <li><strong>전화 상담</strong> — {BIZ['phone_display']}로 증상 말씀해주세요.</li>
    <li><strong>예상 견적 안내</strong> — 출장 전 대략적인 비용을 알려드립니다.</li>
    <li><strong>현장 방문 / 정확한 진단</strong> — {d['name']} 지역 빠르게 출동합니다.</li>
    <li><strong>시공 및 마감 청소</strong> — 깔끔하게 마무리해드립니다.</li>
    <li><strong>사후 A/S</strong> — 문제 발생 시 빠른 재방문 보장.</li>
  </ol>
"""
                html += cta_box_html(
                    f"{d['name']} {s['name']} 작업, 지금 전화 한 통으로 해결하세요."
                )

                # 다른 서비스 안내 (내부 링크 — SEO에 매우 중요)
                html += f"<h2>{d['name']}에서 가능한 다른 서비스</h2><div class='region-tags'>"
                for other in SERVICES:
                    if other["slug"] != s["slug"]:
                        html += f'<a href="/{d["slug"]}-{other["slug"]}/" class="region-tag">{d["name"]} {other["name"]}</a>'
                html += "</div>"

                html += "</article>"
                html += footer_html()
                write_file(DIST_DIR / slug / "index.html", html)
                count += 1
    print(f"  ✓ 지역×서비스 페이지 {count}개 생성")


# ============================================================
# 3. 작업 후기 페이지 생성
# ============================================================
def load_posts():
    if not POSTS_DIR.exists():
        return []
    posts = []
    for f in sorted(POSTS_DIR.glob("*.json"), reverse=True):
        with open(f, "r", encoding="utf-8") as fp:
            posts.append(json.load(fp))
    return posts


def build_post_pages():
    posts = load_posts()
    for p in posts:
        title = f"{p['title']} | {BIZ['name']}"
        desc = p.get("description", p["title"])
        html = head_html(title, desc, f"/post/{p['slug']}/", p.get("thumbnail"))
        html += header_html()
        html += f"""
<section class="post-header">
  <h1>{p['title']}</h1>
  <div class="post-meta">
    <span>📍 {p.get('region', '')}</span>
    <span>📅 {p.get('date', '')}</span>
    <span>🔧 {p.get('service_name', '')}</span>
  </div>
</section>

<article class="post-content">
{p.get('body_html', '')}
"""
        html += cta_box_html()
        html += "</article>"
        html += footer_html()
        write_file(DIST_DIR / "post" / p["slug"] / "index.html", html)
    print(f"  ✓ 후기 페이지 {len(posts)}개 생성")


# ============================================================
# 4. sitemap.xml + robots.txt 자동 생성
# ============================================================
def build_sitemap():
    urls = ["/"]
    for region_key, region_data in REGIONS.items():
        for d in region_data["districts"]:
            for s in SERVICES:
                urls.append(f"/{d['slug']}-{s['slug']}/")
    for p in load_posts():
        urls.append(f"/post/{p['slug']}/")

    today = datetime.now().strftime("%Y-%m-%d")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url>\n    <loc>{SITE_URL}{u}</loc>\n    <lastmod>{today}</lastmod>\n  </url>\n"
    xml += "</urlset>\n"
    write_file(DIST_DIR / "sitemap.xml", xml)
    print(f"  ✓ sitemap.xml ({len(urls)}개 URL)")


def build_robots():
    content = f"""User-agent: *
Allow: /

User-agent: Yeti
Allow: /

User-agent: NaverBot
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    write_file(DIST_DIR / "robots.txt", content)
    print("  ✓ robots.txt")


# ============================================================
# 유틸
# ============================================================
def write_file(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def compress_image(src_path, dest_path):
    """
    이미지 자동 압축 + 크기 조정
    - 가로 1600px 초과 시 자동 축소
    - JPEG 품질 82로 압축
    - 평균 70~90% 용량 감소
    """
    if not PIL_AVAILABLE:
        # Pillow 없으면 그냥 복사
        shutil.copy2(src_path, dest_path)
        return

    try:
        img = Image.open(src_path)

        # EXIF 회전 정보 반영 (휴대폰으로 찍은 사진이 옆으로 누운 문제 해결)
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # RGBA → RGB 변환 (JPEG 저장을 위해)
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 가로 폭이 1600 초과면 비율 유지하며 축소
        if img.width > IMG_MAX_WIDTH:
            ratio = IMG_MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            img = img.resize((IMG_MAX_WIDTH, new_height), Image.LANCZOS)

        # JPEG로 저장 (확장자가 PNG여도 JPEG로 변환됨 — 용량 효율)
        dest_path = Path(dest_path)
        if dest_path.suffix.lower() == ".png":
            dest_path = dest_path.with_suffix(".jpg")

        img.save(dest_path, "JPEG", quality=IMG_QUALITY, optimize=True, progressive=True)

    except Exception as e:
        # 압축 실패 시 원본 그대로 복사 (사이트가 깨지지 않도록)
        print(f"  ⚠️  이미지 압축 실패, 원본 복사: {src_path.name} ({e})")
        shutil.copy2(src_path, dest_path)


def copy_assets():
    """assets 폴더 복사하면서 이미지는 자동 압축"""
    dest = DIST_DIR / "assets"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    img_count = 0
    img_total_before = 0
    img_total_after = 0
    other_count = 0

    for src_file in ASSETS_SRC.rglob("*"):
        if not src_file.is_file():
            continue

        rel_path = src_file.relative_to(ASSETS_SRC)
        dest_file = dest / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        # 이미지면 압축, 아니면 그냥 복사
        if src_file.suffix.lower() in IMG_EXTENSIONS:
            size_before = src_file.stat().st_size
            img_total_before += size_before
            compress_image(src_file, dest_file)
            # PNG가 JPG로 바뀌었을 수도 있으니 다시 찾기
            actual_dest = dest_file
            if not actual_dest.exists() and dest_file.suffix.lower() == ".png":
                actual_dest = dest_file.with_suffix(".jpg")
            if actual_dest.exists():
                img_total_after += actual_dest.stat().st_size
            img_count += 1
        else:
            shutil.copy2(src_file, dest_file)
            other_count += 1

    if img_count > 0 and img_total_before > 0:
        saved_pct = 100 * (1 - img_total_after / img_total_before)
        before_mb = img_total_before / (1024 * 1024)
        after_mb = img_total_after / (1024 * 1024)
        print(f"  ✓ assets/ 복사 완료 (이미지 {img_count}장: {before_mb:.1f}MB → {after_mb:.1f}MB, {saved_pct:.0f}% 절감)")
    else:
        print(f"  ✓ assets/ 복사 완료 (이미지 {img_count}장, 기타 {other_count}개)")


# ============================================================
# 메인 빌드
# ============================================================
def main():
    print("=" * 50)
    print(f"  {BIZ['name']} — 사이트 빌드 시작")
    print("=" * 50)

    # dist 초기화
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    copy_assets()
    build_index()
    print("  ✓ 메인 페이지 (index.html)")
    build_region_service_pages()
    build_post_pages()
    build_sitemap()
    build_robots()

    print("=" * 50)
    print(f"  ✅ 빌드 완료 → {DIST_DIR}")
    print("  GitHub에 dist/ 폴더 push하면 끝!")
    print("=" * 50)


if __name__ == "__main__":
    main()
