from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from core.config import parse_json_or_yaml, requirements_schema, try_parse
from core.search.engine import search_best

HOST = "0.0.0.0"
PORT = 8501

HTML = """
<!doctype html>
<html>
<head><meta charset='utf-8'><title>Stardew Seed Finder</title></head>
<body style="font-family:Arial;margin:20px;max-width:1100px">
<h1>Stardew Seed Finder</h1>
<p>1) Definir Requisitos (JSON; YAML opcional com PyYAML)</p>
<textarea id="cfg" style="width:100%;height:320px"></textarea><br/>
<button onclick="validateCfg()">Validar</button>
<button onclick="showSchema()">Schema</button>
<button onclick="runSearch()">Executar</button>
<pre id="status"></pre>
<h2>Resultados</h2>
<div id="results"></div>
<script>
async function post(path, body){
  const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  return await r.json();
}
async function validateCfg(){
  const r=await post('/validate',{raw:document.getElementById('cfg').value});
  document.getElementById('status').textContent=JSON.stringify(r,null,2);
}
async function showSchema(){
  const r=await fetch('/schema');
  document.getElementById('status').textContent=JSON.stringify(await r.json(),null,2);
}
async function runSearch(){
  document.getElementById('status').textContent='Executando...';
  const r=await post('/run',{raw:document.getElementById('cfg').value});
  document.getElementById('status').textContent='Concluído';
  const rows=(r.results||[]).map(x=>`<tr><td>${x.seed}</td><td>${x.score}</td><td>${(x.unsupported||[]).join(',')}</td></tr>`).join('');
  document.getElementById('results').innerHTML=`<table border='1' cellpadding='6'><tr><th>Seed</th><th>Score</th><th>Não suportado</th></tr>${rows}</table><p><a href='/download/results.json'>Download JSON</a> | <a href='/download/results.csv'>Download CSV</a></p>`;
}
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    last_results: list[dict] = []

    def _json(self, data: dict, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/schema":
            self._json(requirements_schema())
        elif path.startswith("/download/"):
            name = path.split("/")[-1]
            Path(name).write_text(json.dumps(self.last_results, indent=2) if name.endswith(".json") else _to_csv(self.last_results))
            body = Path(name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f"attachment; filename={name}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        raw = payload.get("raw", "")

        if self.path == "/validate":
            try:
                data = parse_json_or_yaml(raw)
                _, err = try_parse(data)
                self._json({"ok": err is None, "error": err})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, status=400)
        elif self.path == "/run":
            try:
                data = parse_json_or_yaml(raw)
                cfg, err = try_parse(data)
                if err:
                    self._json({"ok": False, "error": err}, status=400)
                    return
                results = search_best(cfg.model_dump())
                self.last_results = results
                self._json({"ok": True, "results": results})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, status=500)
        else:
            self.send_error(404)


def _to_csv(results: list[dict]) -> str:
    lines = ["seed,score,hard_passed,unsupported"]
    for r in results:
        lines.append(f"{r['seed']},{r['score']},{r['hard_passed']},\"{';'.join(r['unsupported'])}\"")
    return "\n".join(lines)


def run() -> None:
    sample = Path("examples/community_center_early.json")
    if sample.exists():
        print("Use este exemplo como base:", sample)
    print(f"Open http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    run()
