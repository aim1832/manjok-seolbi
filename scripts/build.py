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
  "areaServed": ["김해시", "창원시"],
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
    <a href="/" class="logo">만<span>족</span>설비</a>
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
  <h1>김해·창원 배관설비 전문<br>{BIZ['name']}</h1>
  <p class="subtitle">하수구 막힘 · 수전 교체 · 변기/세면대 수리 · 욕조 배수구<br>김해·창원 전지역 24시간 출장</p>
  <div class="cta-group">
    <a href="tel:{BIZ['phone_tel']}" class="btn btn-primary">📞 {BIZ['phone_display']}</a>
    <a href="{BIZ['kakao_url']}" target="_blank" class="btn btn-kakao">💬 카톡 상담</a>
    <a href="#services" class="btn btn-secondary">서비스 보기</a>
  </div>
  <p class="hero-tip">💡 카톡으로 사진 보내주시면 빠른 견적 안내!</p>
</section>
"""

    # 서비스
    html += '<section id="services" class="container">'
    html += '<h2 class="section-title">주요 서비스</h2>'
    html += '<p class="section-subtitle">김해·창원 어디든 빠르게 출동합니다</p>'
    html += '<div class="services-grid">'
    for s in SERVICES:
        html += f"""
  <div class="service-card">
    <div class="service-icon">{s['icon']}</div>
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
def build_region_service_pages():
    """예: /jangyu1-drain-clog/ → 장유1동 하수구 막힘 페이지"""
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
