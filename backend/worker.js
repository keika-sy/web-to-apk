// Web to APK — backend tipis (Cloudflare Worker)
//
// Tugasnya cuma dua: memicu GitHub Actions (workflow_dispatch) dan membaca
// status run terakhir. Token GitHub TIDAK pernah dikirim ke browser — token
// disimpan sebagai secret Worker.
//
// Deploy:
//   1. cd backend && npx wrangler deploy
//   2. npx wrangler secret put GH_TOKEN     (fine-grained PAT: repo web-to-apk, Actions: read+write)
//   3. (opsional) ubah ALLOWED_ORIGIN di bawah / wrangler.toml vars
//   4. Salin URL Worker hasil deploy ke docs/index.html -> const BACKEND_URL

const GH_OWNER = "keika-sy";
const GH_REPO = "web-to-apk";
const WORKFLOW_FILE = "build-apk.yml";
const ALLOWED_ORIGIN = "*"; // ganti dengan domain web kamu kalau sudah ada

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}
function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}
function gh(env, path, options = {}) {
  return fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "web-to-apk-worker",
      ...(options.headers || {}),
    },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: corsHeaders() });
    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === "/build") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "Body bukan JSON" }, 400); }
      const { web_url, app_name, package_id, icon_url = "", theme_color = "#2563EB" } = body || {};
      if (!web_url || !app_name || !package_id) return json({ error: "web_url, app_name, package_id wajib diisi" }, 400);
      if (!/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$/.test(String(package_id).toLowerCase()))
        return json({ error: "Package ID tidak valid" }, 400);
      if (!/^https?:\/\//i.test(web_url) && !/^[^\s]+\.[^\s]+/.test(web_url))
        return json({ error: "URL tidak valid" }, 400);

      const res = await gh(env, `/actions/workflows/${WORKFLOW_FILE}/dispatches`, {
        method: "POST",
        body: JSON.stringify({
          ref: "main",
          inputs: {
            web_url: String(web_url),
            app_name: String(app_name).slice(0, 50),
            package_id: String(package_id).toLowerCase(),
            icon_url: String(icon_url || ""),
            theme_color: String(theme_color || "#2563EB"),
          },
        }),
      });
      if (res.status !== 204) {
        const text = await res.text();
        return json({ error: `GitHub menolak trigger (${res.status}): ${text.slice(0, 300)}` }, 502);
      }
      return json({ ok: true, actions_url: `https://github.com/${GH_OWNER}/${GH_REPO}/actions/workflows/${WORKFLOW_FILE}` });
    }

    if (request.method === "GET" && url.pathname === "/status") {
      const res = await gh(env, `/actions/workflows/${WORKFLOW_FILE}/runs?per_page=5`);
      if (!res.ok) return json({ error: `GitHub status ${res.status}` }, 502);
      const data = await res.json();
      const runs = (data.workflow_runs || []).map((r) => ({
        run_number: r.run_number, status: r.status, conclusion: r.conclusion,
        html_url: r.html_url, created_at: r.created_at,
      }));
      return json({ runs });
    }

    return json({ error: "Not found" }, 404);
  },
};
