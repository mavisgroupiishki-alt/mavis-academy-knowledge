const ALLOWED_KEYS = new Set([
  "academy:trainee-curriculum",
  "academy:document-overrides",
  "academy:library-catalog",
  "academy:trainee-submissions",
  "academy:material-metadata",
  "academy:revisions",
  "academy:events",
]);

const json = (value, status = 200) => new Response(JSON.stringify(value), {
  status,
  headers: { "content-type": "application/json; charset=utf-8" },
});

export default {
  async scheduled(_event, _env, ctx) {
    ctx.waitUntil(
      fetch("https://mavis-academy.onrender.com/healthz", {
        headers: { "user-agent": "Mavis-Academy-Uptime/1.0" },
      }).then(response => {
        if (!response.ok) throw new Error(`healthz_${response.status}`);
      }),
    );
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/state") return json({ error: "not_found" }, 404);
    if (request.headers.get("X-Academy-State-Token") !== env.ACADEMY_STATE_TOKEN) {
      return json({ error: "unauthorized" }, 401);
    }

    const key = url.searchParams.get("key");
    if (!ALLOWED_KEYS.has(key)) return json({ error: "invalid_key" }, 400);

    if (request.method === "GET") {
      const row = await env.DB.prepare("SELECT value FROM academy_state WHERE key = ?1")
        .bind(key).first();
      return json({ value: row ? JSON.parse(row.value) : null });
    }

    if (request.method === "PUT") {
      let payload;
      try {
        payload = await request.json();
      } catch {
        return json({ error: "invalid_json" }, 400);
      }
      if (!payload || typeof payload.value !== "object" || payload.value === null) {
        return json({ error: "invalid_value" }, 400);
      }
      await env.DB.prepare(
        "INSERT INTO academy_state (key, value, updated_at) VALUES (?1, ?2, datetime('now')) "
        + "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')",
      ).bind(key, JSON.stringify(payload.value)).run();
      return json({ value: payload.value });
    }

    return json({ error: "method_not_allowed" }, 405);
  },
};
