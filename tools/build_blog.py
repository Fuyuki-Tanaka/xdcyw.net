#!/usr/bin/env python3
"""Minimal static blog generator for xdcyw.net.

Usage: python3 tools/build_blog.py

Reads posts/*.md (filename: YYYY-MM-DD-slug.md, with a small front matter
block of `title:` / `description:` lines between --- markers), renders each
post to blog/<date>-<slug>/index.html and rebuilds blog/index.html.
No third-party dependencies.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
BLOG_DIR = ROOT / "blog"

SITE_NAME = "田中 志"
BLOG_TITLE = "ブログ"
BLOG_SUB = "考えたこと、作ったもの、日々の記録。"

PAGE_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #f6f5f2; --surface: #ffffff; --text: #16161a; --sub: #6b6b70;
  --border: #e7e4dc; --accent: #b3402a; --tile: #f1efe9;
  --shadow: 0 12px 40px rgba(30, 25, 20, .07);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101014; --surface: #17171c; --text: #ececec; --sub: #9a9aa2;
    --border: #26262e; --accent: #e0684e; --tile: #1f1f26;
    --shadow: 0 12px 40px rgba(0, 0, 0, .45);
  }
}
body {
  background: var(--bg);
  background-image: radial-gradient(rgba(120, 110, 90, .13) 1px, transparent 1px);
  background-size: 22px 22px;
  color: var(--text);
  font-family: 'Inter', 'Noto Sans JP', sans-serif;
  font-size: 15px; line-height: 1.7;
  display: flex; flex-direction: column; align-items: center;
  padding: 48px 20px; min-height: 100vh;
}
.wrap { width: 100%; max-width: 680px; }
header.site { margin-bottom: 28px; }
header.site a.home {
  color: var(--sub); text-decoration: none; font-size: 13px;
}
header.site a.home:hover { color: var(--accent); }
h1.blog-title {
  font-family: 'Noto Serif JP', serif;
  font-size: 26px; font-weight: 700; letter-spacing: .02em; margin-top: 10px;
}
p.blog-sub { color: var(--sub); font-size: 14px; margin-top: 4px; }
.post-list { display: flex; flex-direction: column; gap: 10px; }
.post-item {
  display: block; background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px; text-decoration: none; color: var(--text);
  box-shadow: var(--shadow);
  transition: border-color .15s, transform .15s;
}
.post-item:hover { border-color: var(--accent); transform: translateX(3px); }
.post-date { font-size: 12px; color: var(--sub); }
.post-name { font-size: 16px; font-weight: 600; margin-top: 2px; }
.post-desc { font-size: 13px; color: var(--sub); margin-top: 2px; }
article {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 18px; padding: 40px 36px; box-shadow: var(--shadow);
}
article .date { font-size: 13px; color: var(--sub); }
article h1 {
  font-family: 'Noto Serif JP', serif;
  font-size: 25px; font-weight: 700; line-height: 1.4; margin: 6px 0 28px;
}
article h2 {
  font-family: 'Noto Serif JP', serif;
  font-size: 19px; font-weight: 700; margin: 32px 0 12px;
}
article h3 { font-size: 16px; font-weight: 700; margin: 24px 0 10px; }
article p { margin: 0 0 16px; line-height: 1.9; }
article ul, article ol { margin: 0 0 16px 1.4em; line-height: 1.9; }
article blockquote {
  border-left: 3px solid var(--accent); padding-left: 14px;
  color: var(--sub); margin: 0 0 16px;
}
article code {
  background: var(--tile); border-radius: 4px; padding: 1px 5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
}
article pre {
  background: #0d0d12; color: #e8e8e8; border-radius: 8px;
  padding: 16px; overflow-x: auto; margin: 0 0 16px;
}
article pre code { background: none; padding: 0; color: inherit; }
article a { color: var(--accent); }
article hr { border: none; border-top: 1px solid var(--border); margin: 28px 0; }
article img { max-width: 100%; border-radius: 8px; }
nav.post-nav { margin-top: 24px; font-size: 14px; }
nav.post-nav a { color: var(--sub); text-decoration: none; }
nav.post-nav a:hover { color: var(--accent); }
footer { margin-top: 24px; font-size: 12px; color: var(--sub); opacity: .6; text-align: center; }
@media (max-width: 560px) { article { padding: 28px 20px; } }
"""

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Noto+Serif+JP:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">"""


def inline(md: str) -> str:
    s = html.escape(md)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def render_markdown(md: str) -> str:
    out, para, lst = [], [], None

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            out.append(f"<{tag}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{tag}>")
            lst = None

    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            flush_para(); flush_list()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
        elif re.match(r"^#{1,3}\s", line):
            flush_para(); flush_list()
            level = len(line) - len(line.lstrip("#"))
            out.append(f"<h{level}>" + inline(line[level:].strip()) + f"</h{level}>")
        elif line.strip() == "---":
            flush_para(); flush_list()
            out.append("<hr>")
        elif line.startswith("> "):
            flush_para(); flush_list()
            out.append("<blockquote><p>" + inline(line[2:]) + "</p></blockquote>")
        elif re.match(r"^[-*]\s", line):
            flush_para()
            if not lst or lst[0] != "ul":
                flush_list(); lst = ("ul", [])
            lst[1].append(line[2:])
        elif re.match(r"^\d+\.\s", line):
            flush_para()
            if not lst or lst[0] != "ol":
                flush_list(); lst = ("ol", [])
            lst[1].append(re.sub(r"^\d+\.\s", "", line))
        elif line.strip() == "":
            flush_para(); flush_list()
        else:
            flush_list()
            para.append(line.strip())
        i += 1
    flush_para(); flush_list()
    return "\n".join(out)


def parse_post(path: Path):
    text = path.read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for kv in text[3:end].split("\n"):
                if ":" in kv:
                    k, v = kv.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = text[end + 4:].lstrip("\n")
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)", path.stem)
    date, slug = (m.group(1), m.group(2)) if m else ("", path.stem)
    return {
        "date": meta.get("date", date),
        "slug": slug,
        "title": meta.get("title", slug),
        "description": meta.get("description", ""),
        "body_html": render_markdown(body),
    }


def post_page(p) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(p['title'])} | {BLOG_TITLE} | {SITE_NAME}</title>
<meta name="description" content="{html.escape(p['description'])}">
<link rel="icon" href="/assets/momo.svg" type="image/svg+xml">
{FONTS}
<style>{PAGE_CSS}</style>
</head>
<body>
<div class="wrap">
<header class="site"><a class="home" href="/">← {SITE_NAME} トップ</a></header>
<article>
<div class="date">{p['date']}</div>
<h1>{html.escape(p['title'])}</h1>
{p['body_html']}
</article>
<nav class="post-nav"><a href="/blog/">← 記事一覧へ</a></nav>
<footer>© 2026 田中 芙雪</footer>
</div>
</body>
</html>
"""


def index_page(posts) -> str:
    items = "\n".join(
        f"""<a class="post-item" href="/blog/{p['date']}-{p['slug']}/">
<div class="post-date">{p['date']}</div>
<div class="post-name">{html.escape(p['title'])}</div>
{f'<div class="post-desc">{html.escape(p["description"])}</div>' if p['description'] else ''}
</a>"""
        for p in posts
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{BLOG_TITLE} | {SITE_NAME}</title>
<meta name="description" content="{BLOG_SUB}">
<link rel="icon" href="/assets/momo.svg" type="image/svg+xml">
{FONTS}
<style>{PAGE_CSS}</style>
</head>
<body>
<div class="wrap">
<header class="site"><a class="home" href="/">← {SITE_NAME} トップ</a></header>
<h1 class="blog-title">{BLOG_TITLE}</h1>
<p class="blog-sub">{BLOG_SUB}</p>
<div class="post-list" style="margin-top:24px;">
{items}
</div>
<footer>© 2026 田中 芙雪</footer>
</div>
</body>
</html>
"""


def main():
    files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    if not files:
        print("no posts found", file=sys.stderr)
        return 1
    posts = [parse_post(f) for f in files]
    for p in posts:
        out_dir = BLOG_DIR / f"{p['date']}-{p['slug']}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(post_page(p), encoding="utf-8")
        print("built", out_dir.relative_to(ROOT) / "index.html")
    BLOG_DIR.mkdir(exist_ok=True)
    (BLOG_DIR / "index.html").write_text(index_page(posts), encoding="utf-8")
    print("built blog/index.html with", len(posts), "post(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
