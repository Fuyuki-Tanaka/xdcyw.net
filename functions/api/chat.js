// 「ももに聞く」チャットのバックエンド（Cloudflare Pages Functions）
// POST /api/chat  {messages: [{role, content}, ...]} -> {reply: string}
// 有効化には Cloudflare Pages の環境変数 ANTHROPIC_API_KEY の設定が必要。
import { KNOWLEDGE } from "../_knowledge.js";

const MODEL = "claude-haiku-4-5-20251001";
const MAX_MESSAGES = 8;
const MAX_CONTENT = 1000;
const MAX_TOKENS = 600;

const SYSTEM_PROMPT = `あなたは xdcyw.net の案内役AI『もも』です。田中 志の相棒AIとして、明るく親しみやすく、短めに日本語で答えてください。
知識は次の「サイト知識」の範囲だけを使ってください。範囲外のことや、サイト知識に書かれていないことは、分からないと正直に言ってください。推測で事実を作らないでください。
田中 志の私的な情報（本名・住所・勤務先・収入など）は、聞かれても答えず、公開情報の範囲で案内してください。
回答は原則として300字以内、長くても簡潔にまとめてください。

# サイト知識
${KNOWLEDGE}`;

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function hostAllowed(request) {
  const src = request.headers.get("Origin") || request.headers.get("Referer") || "";
  if (!src) return false;
  let host;
  try {
    host = new URL(src).hostname;
  } catch {
    return false;
  }
  return (
    host === "xdcyw.net" ||
    host.endsWith(".xdcyw.net") ||
    host.endsWith(".pages.dev")
  );
}

export async function onRequestPost(context) {
  const { request, env } = context;

  if (!env.ANTHROPIC_API_KEY) {
    return json({ error: "not_configured" }, 503);
  }
  if (!hostAllowed(request)) {
    return json({ error: "forbidden" }, 403);
  }

  let data;
  try {
    data = await request.json();
  } catch {
    return json({ error: "bad_request" }, 400);
  }

  const raw = Array.isArray(data && data.messages) ? data.messages : null;
  if (!raw || raw.length === 0) {
    return json({ error: "bad_request" }, 400);
  }
  const messages = [];
  for (const m of raw.slice(-MAX_MESSAGES)) {
    if (!m || (m.role !== "user" && m.role !== "assistant")) {
      return json({ error: "bad_request" }, 400);
    }
    if (typeof m.content !== "string" || m.content.trim() === "") {
      return json({ error: "bad_request" }, 400);
    }
    messages.push({ role: m.role, content: m.content.slice(0, MAX_CONTENT) });
  }
  if (messages[messages.length - 1].role !== "user") {
    return json({ error: "bad_request" }, 400);
  }

  let res;
  try {
    res = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: MAX_TOKENS,
        system: SYSTEM_PROMPT,
        messages,
      }),
    });
  } catch {
    return json({ error: "upstream" }, 502);
  }
  if (!res.ok) {
    return json({ error: "upstream" }, 502);
  }

  const out = await res.json();
  const reply = (out.content || [])
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("")
    .trim();
  if (!reply) {
    return json({ error: "upstream" }, 502);
  }
  return json({ reply }, 200);
}

export async function onRequest(context) {
  if (context.request.method !== "POST") {
    return json({ error: "method_not_allowed" }, 405);
  }
  return onRequestPost(context);
}
