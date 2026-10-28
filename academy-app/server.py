from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import os
import time
from urllib.parse import urlparse, parse_qs, quote

ROOT = Path(__file__).resolve().parent
REPO_API = "https://api.github.com/repos/mavisgroupiishki-alt/mavis-academy-knowledge"
CACHE = {"at": 0, "data": None}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def respond_json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/ai/grade":
            return self.respond_json({"error": "not_found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 12000:
                return self.respond_json({"error": "invalid_size"}, 413)
            payload = json.loads(self.rfile.read(length))
            answer = str(payload.get("answer", ""))[:4500]
            task = str(payload.get("task", ""))[:2200]
            criteria = payload.get("criteria", [])
            if not isinstance(criteria, list) or len(criteria) > 20:
                return self.respond_json({"error": "invalid_rubric"}, 400)
            token = os.getenv("ACADEMY_AI_TOKEN", "")
            if not token:
                return self.respond_json({"mode": "not_configured", "message": "AI provider is not configured"})
            endpoint = os.getenv("ACADEMY_AI_URL", "https://api.openai.com/v1/chat/completions")
            # Restricted to a configured endpoint; credentials never reach the browser.
            model = os.getenv("ACADEMY_AI_MODEL", "gpt-4.1-mini")
            system = ("Ты проверяешь ответ стажёра Mavis Group по учебному заданию. "
                      "Оцени фактическую полноту и понятность. Не считай совпадение ключевых слов достаточным. "
                      "Дай конструктивный конкретный отзыв на русском, 2-5 предложений. "
                      "Ответь ТОЛЬКО JSON с полями passed (boolean), feedback (string). "
                      "Порог зачёта — нет существенных ошибок, раскрыты основные критерии.")
            body = json.dumps({"model": model,"temperature": 0.2,"response_format": {"type":"json_object"},
                               "messages":[{"role":"system","content":system},
                                           {"role":"user","content":json.dumps({"task":task,"rubric":criteria,"answer":answer},ensure_ascii=False)}]}).encode()
            req = Request(endpoint, data=body, headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"}, method="POST")
            with urlopen(req, timeout=25) as response:
                outer = json.load(response)
            inner = json.loads(outer["choices"][0]["message"]["content"])
            return self.respond_json({"mode":"ai","passed":bool(inner.get("passed")),"feedback":str(inner.get("feedback", ""))[:1200]})
        except Exception:
            return self.respond_json({"mode":"unavailable","message":"AI grader temporarily unavailable"}, 503)

    def get_knowledge_document(self):
        query = parse_qs(urlparse(self.path).query)
        path = query.get("path", [""])[0]
        # Only read known instructional directories, never arbitrary URLs or local paths.
        allowed = ("02 PRODUCTS/", "03 SALES/", "04 EXPERT/", "06 BITRIX24/", "09 SOP/")
        if not path.startswith(allowed) or not path.endswith(".md") or ".." in path or "\\" in path:
            return self.respond_json({"error":"not_allowed"}, 400)
        url = "https://raw.githubusercontent.com/mavisgroupiishki-alt/mavis-academy-knowledge/main/" + "/".join(quote(p, safe="") for p in path.split("/"))
        try:
            req = Request(url, headers={"User-Agent":"Mavis-Academy"})
            with urlopen(req, timeout=12) as response:
                data = response.read(350000).decode("utf-8")
            return self.respond_json({"path":path,"content":data})
        except Exception:
            return self.respond_json({"error":"unavailable"}, 503)

    def do_GET(self):
        if self.path.startswith("/api/knowledge/document?"):
            return self.get_knowledge_document()
        if self.path.startswith("/api/knowledge/status"):
            if CACHE["data"] and time.time() - CACHE["at"] < 300:
                return self.respond_json(CACHE["data"])
            try:
                request = Request(REPO_API + "/commits/main", headers={"User-Agent": "Mavis-Academy-MVP", "Accept": "application/vnd.github+json"})
                with urlopen(request, timeout=7) as response:
                    obj = json.load(response)
                data = {"connected": True, "commit": obj.get("sha", "")[:10], "updated": obj.get("commit", {}).get("committer", {}).get("date"), "source": "GitHub / Mavis Knowledge"}
                CACHE.update({"at": time.time(), "data": data})
                return self.respond_json(data)
            except (URLError, HTTPError, TimeoutError, ValueError) as exc:
                return self.respond_json({"connected": False, "message": "Источник временно недоступен"}, 503)
        if self.path == "/healthz":
            return self.respond_json({"ok": True})
        if self.path in ("/", "/index.html"):
            self.path = "/index.html"
        return super().do_GET()

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"Mavis Academy on port {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
