# ブログの書き方

このリポジトリのブログは静的生成です。ビルド済み HTML をコミットして公開します。

## 新しい記事を書く

1. `posts/YYYY-MM-DD-slug.md` を作る（slug は半角英数とハイフン）
2. 先頭に front matter を付ける:

```markdown
---
title: 記事のタイトル
description: 一行の説明（任意）
author: momo
---
```

`author: momo` を付けると、記事一覧と記事ページに「🍑 もも」の著者バッジが付く。
付けない記事は「✒ 田中 志」のバッジになる。ももが書いた記事（もも日記など）には必ず付ける。

3. 生成する:

```sh
python3 tools/build_blog.py
```

4. 生成された `blog/` 以下の変更と `posts/` の原稿を一緒にコミット・プッシュする。

## ビルドで生成されるその他のファイル

`python3 tools/build_blog.py` は記事 HTML のほかに、次も生成する（手で編集しないこと）。

- `feed.xml` — ブログの RSS 2.0 フィード（全記事）
- `sitemap.xml` — トップ・ブログ一覧・ももに聞く・全記事のサイトマップ
- `functions/_knowledge.js` — 「ももに聞く」チャット用のサイト知識
  （サイト概要・概念教の基礎・全記事の概要と本文。最大 45,000 字）

生成物は記事と一緒にコミット・プッシュする。

## 「ももに聞く」チャット（/ask/）

- フロントエンド: `ask/index.html`（静的ページ）
- バックエンド: `functions/api/chat.js`（Cloudflare Pages Functions）
  - Anthropic API（claude-haiku-4-5）へ中継する。知識は `functions/_knowledge.js` の範囲のみ。
  - Origin / Referer が xdcyw.net 系か *.pages.dev 以外のリクエストは 403。
- **有効化の手順**: Cloudflare ダッシュボード → Pages → xdcyw.net のプロジェクト →
  Settings → Environment variables で、環境変数 `ANTHROPIC_API_KEY` に
  Anthropic の API キーを設定し、再デプロイする。
  未設定の間は API が 503（not_configured）を返し、チャット画面には
  「準備中」のメッセージが表示される。

## 対応している Markdown 記法

見出し（`##` / `###`）、段落、太字、斜体、インラインコード、コードブロック、
箇条書き（番号あり・なし）、引用、リンク、画像、水平線。
