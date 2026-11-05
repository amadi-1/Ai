#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سرور محلی اپ آپشن - نسخه اصلاح‌شده (gzip + direct tsev2)
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import ssl
import os
import sys
import traceback
import gzip
import zlib
from pathlib import Path

PORT = 8080
DIR = Path(__file__).parent.resolve()

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
    "Accept-Encoding": "identity",
    "Connection": "close",
}

REFERER_MAP = {
    "tsetmc.com": "https://www.tsetmc.com/",
    "cdn.tsetmc.com": "https://www.tsetmc.com/",
    "old.tsetmc.com": "https://old.tsetmc.com/",
    "chartix.ir": "https://chartix.ir/",
    "api.chartix.ir": "https://chartix.ir/",
    "data.chartix.ir": "https://chartix.ir/",
    "nobitex.ir": "https://nobitex.ir/",
    "tgju.org": "https://www.tgju.org/",
    "codal.ir": "https://www.codal.ir/",
}

SOFT_FAIL = (
    "persiancalapi", "holidayapi", "binance.com", "stooq.com",
    "milli.gold", "gold-api.com", "oilprice.com", "fonts.googleapis",
    "fonts.gstatic"
)

TIMEOUT_DEFAULT = 20
TIMEOUT_BULK = 45


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def log_message(self, fmt, *args):
        try:
            msg = fmt % args
        except Exception:
            msg = str(args)
        p = getattr(self, "path", "")
        if p.startswith("/proxy/") or p.startswith("/tsev2/"):
            print(f"[PROXY] {getattr(self, 'command', '?')} {p[:120]}")
        else:
            print(f"[HTTP ] {msg}")

    def end_headers(self):
        try:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Cache-Control", "no-store")
        except Exception:
            pass
        super().end_headers()

    def do_OPTIONS(self):
        try:
            self.send_response(204)
            self.end_headers()
        except Exception:
            pass

    def do_GET(self):
        try:
            if self.path.startswith("/tsev2/"):
                return self.proxy_url("https://old.tsetmc.com" + self.path, bulk=True)
            if self.path.startswith("/proxy/"):
                return self.handle_proxy()
            if self.path in ("/", "/index.html", "/index.htm"):
                self.path = "/index.html"
            return super().do_GET()
        except Exception as e:
            print(f"[ERR GET] {e}")
            traceback.print_exc()
            self._send_empty(500)

    def do_HEAD(self):
        try:
            return super().do_HEAD()
        except Exception:
            self._send_empty(500)

    def do_POST(self):
        try:
            if self.path.startswith("/proxy/"):
                return self.handle_proxy()
            self.send_error(404)
        except Exception as e:
            print(f"[ERR POST] {e}")
            self._send_empty(500)

    def handle_proxy(self):
        try:
            raw = self.path[len("/proxy/"):]
            target = urllib.parse.unquote(raw)
            for _ in range(2):
                if "%25" in target or (target.count("%") > 3 and "http" in target):
                    try:
                        t2 = urllib.parse.unquote(target)
                        if t2.startswith("http"):
                            target = t2
                        else:
                            break
                    except Exception:
                        break
                else:
                    break
            return self.proxy_url(target)
        except Exception as e:
            print(f"[ERR handle_proxy] {e}")
            self._send_empty(502)

    def _decompress(self, data, enc):
        enc = (enc or "").lower()
        if not data:
            return data
        try:
            if enc == "gzip" or data[:2] == b"\x1f\x8b":
                return gzip.decompress(data)
            if enc == "deflate":
                try:
                    return zlib.decompress(data)
                except Exception:
                    return zlib.decompress(data, -zlib.MAX_WBITS)
        except Exception:
            pass
        return data

    def proxy_url(self, target: str, bulk: bool = False):
        soft = any(s in target for s in SOFT_FAIL)
        try:
            if not target.startswith("http://") and not target.startswith("https://"):
                self._send_empty(400)
                return

            parsed = urllib.parse.urlparse(target)
            host = (parsed.hostname or "").lower()

            headers = dict(BROWSER_HEADERS)
            for domain, ref in REFERER_MAP.items():
                if domain in host:
                    headers["Referer"] = ref
                    headers["Origin"] = ref.rstrip("/")
                    break
            else:
                headers["Referer"] = "https://www.tsetmc.com/"
                headers["Origin"] = "https://www.tsetmc.com"

            for h in ("Content-Type", "Authorization"):
                if h in self.headers:
                    headers[h] = self.headers[h]

            body = None
            if self.command == "POST":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    if length > 0:
                        body = self.rfile.read(length)
                except Exception:
                    body = None

            req = urllib.request.Request(target, data=body, headers=headers,
                                         method=self.command or "GET")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(context=ctx),
            )

            timeout = TIMEOUT_BULK if (bulk or "/tsev2/" in target or "MarketWatchInit" in target or "ClientTypeAll" in target) else TIMEOUT_DEFAULT

            with opener.open(req, timeout=timeout) as resp:
                data = resp.read()
                data = self._decompress(data, resp.headers.get("Content-Encoding"))
                ctype = resp.headers.get("Content-Type", "application/octet-stream")
                self.send_response(resp.status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        except urllib.error.HTTPError as e:
            try:
                data = e.read()
            except Exception:
                data = b""
            data = self._decompress(data, e.headers.get("Content-Encoding"))
            if soft:
                self._send_bytes(200, b"{}", "application/json")
            else:
                try:
                    self.send_response(e.code)
                    self.send_header("Content-Type",
                                     e.headers.get("Content-Type", "text/plain; charset=utf-8"))
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    self._send_empty(502)

        except Exception as e:
            print(f"[ERROR] {type(e).__name__}: {e} | {target[:90]}")
            if soft:
                self._send_bytes(200, b"{}", "application/json")
            else:
                self._send_empty(502)

    def _send_empty(self, code):
        try:
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", "0")
            self.end_headers()
        except Exception:
            pass

    def _send_bytes(self, code, data, ctype):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            pass


def inject_proxy_patch(html: str) -> str:
    return html


def main():
    os.chdir(DIR)

    html_path = DIR / "index.html"
    if not html_path.exists():
        print("!!! فایل index.html پیدا نشد.")
        print(f"آن را در کنار server.py قرار بده: {DIR}")
        input("Enter را بزنید برای خروج...")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  سرور اپ آپشن (نسخه اصلاح‌شده gzip)")
    print("=" * 60)
    print(f"  آدرس:  http://127.0.0.1:{PORT}")
    print(f"  آدرس:  http://localhost:{PORT}")
    print()
    print("  این پنجره را باز نگه دارید!")
    print("  برای توقف: Ctrl+C")
    print("=" * 60)
    print()

    try:
        with ThreadingTCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"✓ سرور روی پورت {PORT} در حال اجرا است...")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e) or getattr(e, "winerror", None) == 10048:
            print(f"!!! پورت {PORT} اشغال است.")
            print("برنامه دیگری از این پورت استفاده می‌کند.")
            print("آن را ببند یا کامپیوتر را ریستارت کن.")
        else:
            print(f"!!! خطا در شروع سرور: {e}")
        input("Enter را بزنید برای خروج...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nسرور متوقف شد.")


if __name__ == "__main__":
    main()