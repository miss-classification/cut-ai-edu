// Cloudflare Pages worker for CUT! Best-of-N Studio.
// Serves static files unchanged, adds HTTP Range (206) responses so iPhone and iPad Safari can play the MP4s,
// and applies the same headers as _headers (which Pages does not apply when a _worker.js is present).
const NO_CACHE = new Set(["/", "/index.html", "/evidence", "/evidence.html", "/teaching", "/teaching.html", "/present", "/present.html"]);

function withHeaders(res, path) {
  const h = new Headers(res.headers);
  h.set("X-Content-Type-Options", "nosniff");
  h.set("Referrer-Policy", "strict-origin-when-cross-origin");
  if (NO_CACHE.has(path)) h.set("Cache-Control", "no-cache");
  if (path.endsWith(".mp4")) h.set("Accept-Ranges", "bytes");
  return new Response(res.body, { status: res.status, statusText: res.statusText, headers: h });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const range = request.headers.get("range");
    if (!range || request.method !== "GET" || !url.pathname.endsWith(".mp4")) {
      return withHeaders(await env.ASSETS.fetch(request), url.pathname);
    }
    const res = await env.ASSETS.fetch(new Request(request.url, { method: "GET" }));
    if (res.status !== 200) return withHeaders(res, url.pathname);
    const buf = await res.arrayBuffer();
    const size = buf.byteLength;
    const m = /^bytes=(\d*)-(\d*)$/.exec(range.trim());
    let start, end;
    if (m && m[1] !== "") {
      start = Number(m[1]);
      end = m[2] !== "" ? Math.min(Number(m[2]), size - 1) : size - 1;
    } else if (m && m[2] !== "") {
      start = Math.max(0, size - Number(m[2]));
      end = size - 1;
    }
    const h = new Headers(res.headers);
    h.set("Accept-Ranges", "bytes");
    h.set("X-Content-Type-Options", "nosniff");
    h.set("Referrer-Policy", "strict-origin-when-cross-origin");
    if (start === undefined || start >= size || start > end) {
      h.set("Content-Range", `bytes */${size}`);
      h.delete("Content-Length");
      return new Response(null, { status: 416, headers: h });
    }
    h.set("Content-Range", `bytes ${start}-${end}/${size}`);
    h.set("Content-Length", String(end - start + 1));
    return new Response(buf.slice(start, end + 1), { status: 206, headers: h });
  },
};
