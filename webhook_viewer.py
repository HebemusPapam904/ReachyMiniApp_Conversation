"""Ultra simple local receiver: displays every POST it receives, live, in a web page.

Stands in for the real Shariiing endpoint during local testing of conversation_relay.
No dependencies beyond the Python standard library.

Usage:
    python webhook_viewer.py [port]   # default port 8686

Then:
    - Point RELAY_WEBHOOK_URL at this machine, e.g. http://127.0.0.1:8686/ShariiingClient/sendNote
    - Open http://127.0.0.1:8686/ in a browser to watch messages arrive.
"""

import sys
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_PORT = 8686
MAX_MESSAGES = 200

messages: list[dict] = []
lock = threading.Lock()

PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Webhook Viewer</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 0; padding: 1.5rem; background: #0f1115; color: #e6e6e6; }
  h1 { font-size: 1.1rem; color: #9aa4b2; font-weight: 600; margin: 0 0 1rem; }
  .msg { background: #1a1d24; border-left: 3px solid #6c8cff; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.6rem; }
  .msg.assistant { border-left-color: #4fd1a5; }
  .meta { font-size: 0.75rem; color: #8b93a3; margin-bottom: 0.25rem; }
  .role { text-transform: uppercase; font-weight: 700; letter-spacing: 0.03em; }
  .role.user { color: #6c8cff; }
  .role.assistant { color: #4fd1a5; }
  .text { white-space: pre-wrap; line-height: 1.4; }
  .path { color: #5a6272; font-size: 0.7rem; }
  #empty { color: #5a6272; }
</style>
</head>
<body>
<h1 id="title">Webhook Viewer</h1>
<div id="list"><p id="empty">En attente de messages&hellip;</p></div>
<script>
async function poll() {
  const res = await fetch('/api/messages');
  const data = await res.json();
  if (data.length === 0) return;
  const list = document.getElementById('list');
  list.innerHTML = data.slice().reverse().map(function (m) {
    var cls = m.role === 'assistant' ? 'msg assistant' : 'msg';
    var text = (m.text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;');
    return '<div class="' + cls + '">' +
      '<div class="meta"><span class="role ' + m.role + '">' + m.role + '</span> &middot; ' +
      m.timestamp + ' <span class="path">' + m.path + '</span></div>' +
      '<div class="text">' + text + '</div></div>';
  }).join('');
}
setInterval(poll, 1000);
poll();
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print("[%s] %s" % (self.log_date_time_string(), format % args))

    def do_GET(self):
        if self.path == "/api/messages":
            self._send_json(list(messages))
            return
        self._send_html(PAGE)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b""

        role = "unknown"
        text = raw_body.decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw_body)
            if isinstance(payload, dict):
                role = payload.get("role", "unknown")
                text = payload.get("text", json.dumps(payload, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            pass

        entry = {
            "path": self.path,
            "role": role,
            "text": text,
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        }
        with lock:
            messages.append(entry)
            del messages[:-MAX_MESSAGES]

        self._send_json({"status": "ok"})

    def _send_json(self, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Webhook viewer listening on http://0.0.0.0:{port}/ (open http://127.0.0.1:{port}/ in a browser)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
