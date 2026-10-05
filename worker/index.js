const BASE = "https://raw.githubusercontent.com/arfazca/arfazca/generated";
const REPO = "arfazca/arfazca";
const TZ = "America/Vancouver";
const WIDTH = 1200;
const DAY = 1440;

function local(now) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(now);
  const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
  return { date: `${p.year}-${p.month}-${p.day}`, minute: Number(p.hour) * 60 + Number(p.minute) };
}

async function get(path, ttl) {
  const r = await fetch(`${BASE}/${path}`, { cf: { cacheTtl: ttl, cacheEverything: true } });
  return r.ok ? r.text() : null;
}

function svg(body) {
  return new Response(body, {
    headers: {
      "content-type": "image/svg+xml; charset=utf-8",
      "cache-control": "no-cache, max-age=0",
      "access-control-allow-origin": "*",
    },
  });
}

async function frame(mode, t) {
  const plan = await get(`schedule/${t.date}.json`, 300);
  if (plan) {
    const seg = JSON.parse(plan).segments.find((s) => s.start <= t.minute && t.minute < s.end);
    if (seg) {
      const body = await get(`frames/${t.date}/${seg.state}-${seg.variant}-${mode}.svg`, 600);
      if (body) return svg(body);
    }
  }
  const fallback = await get(`about-${mode}.svg`, 60);
  return fallback ? svg(fallback) : new Response("unavailable", { status: 503 });
}

async function bar(mode, t) {
  const body = (await get(`frames/${t.date}/bar-${mode}.svg`, 600)) ?? (await get(`today-${mode}.svg`, 60));
  if (!body) return new Response("unavailable", { status: 503 });
  const nx = (t.minute / DAY) * WIDTH;
  const xs = [nx - 1.5, Math.min(Math.max(nx, 20), WIDTH - 20)];
  return svg(body.replace(/<g id="now">([\s\S]*?)<\/g>/, (_, inner) => {
    let i = 0;
    return `<g id="now">${inner.replace(/ x="[^"]*"/g, () => ` x="${xs[Math.min(i++, 1)].toFixed(1)}"`)}</g>`;
  }));
}

async function dispatch(env) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/about-me.yml/dispatches`, {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.GH_TOKEN}`,
      accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28",
      "user-agent": "arfazca-banner",
    },
    body: JSON.stringify({ ref: "main" }),
  });
  if (!r.ok) throw new Error(`dispatch failed: ${r.status} ${await r.text()}`);
}

export default {
  async scheduled(event, env) {
    if (env.GH_TOKEN) await dispatch(env);
  },

  async fetch(request) {
    const m = new URL(request.url).pathname.match(/^\/(about|today)-(dark|light)\.svg$/);
    if (!m) return Response.redirect("https://github.com/arfazca", 302);
    const t = local(new Date());
    return m[1] === "about" ? frame(m[2], t) : bar(m[2], t);
  },
};
