# Local static server that behaves like Cloudflare Pages for our URLs: /x -> /x.html, /x/ -> /x/index.html, 404.html,
# and the headers from dist/_headers (so the Content-Security-Policy is tested locally too).
# Usage: python3 scripts/qa/cfserve.py dist 8787 &
import http.server, os, sys, functools, re, io

ROOT = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8787


def load_headers():
    rules, cur = [], None
    p = os.path.join(ROOT, '_headers')
    if not os.path.exists(p):
        return rules
    for line in open(p, encoding='utf-8'):
        if not line.strip():
            continue
        if not line.startswith((' ', '\t')):
            cur = (re.compile('^' + re.escape(line.strip()).replace(r'\*', '.*') + '$'), [])
            rules.append(cur)
        elif cur and ':' in line:
            k, v = line.strip().split(':', 1)
            cur[1].append((k.strip(), v.strip()))
    return rules


RULES = load_headers()


class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split('?', 1)[0]
        for rx, hs in RULES:
            if rx.match(path):
                for k, v in hs:
                    self.send_header(k, v)
        super().end_headers()

    def send_head(self):
        path = self.path.split('?', 1)[0].split('#', 1)[0]
        fs = self.translate_path(path)
        if not os.path.exists(fs) and os.path.exists(fs + '.html'):
            self.path = path + '.html'
        elif not os.path.exists(fs) and not path.endswith('/') and os.path.isdir(fs):
            self.path = path + '/'
        fs2 = self.translate_path(self.path.split('?', 1)[0])
        if not os.path.exists(fs2):
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            body = open(os.path.join(ROOT, '404.html'), 'rb').read() if os.path.exists(os.path.join(ROOT, '404.html')) else b'404'
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        return super().send_head()

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(H, directory=ROOT)).serve_forever()
