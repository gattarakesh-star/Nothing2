from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import base64
import yt_dlp


def build_headers(handler):
    handler.send_response(200)
    handler.send_header("Content-type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.end_headers()


def get_cookie_file():
    cookies_b64 = os.environ.get("YT_COOKIES_B64")
    if not cookies_b64:
        return None
    cookie_path = "/tmp/cookies.txt"
    try:
        with open(cookie_path, "wb") as f:
            f.write(base64.b64decode(cookies_b64))
        return cookie_path
    except Exception:
        return None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        url = query.get("url", [None])[0]

        if not url:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'url' query param"}).encode())
            return

        cookie_file = get_cookie_file()

        # Try a few different YouTube "client" personas in order.
        # YouTube's web client has been intermittently broken; android/tv
        # clients often still work.
        client_attempts = [
            ["android", "web"],
            ["tv_embedded"],
            ["ios"],
            ["web"],
        ]

        last_error = None
        info = None

        for clients in client_attempts:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "extractor_args": {"youtube": {"player_client": clients}},
            }
            if cookie_file:
                ydl_opts["cookiefile"] = cookie_file

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                if info and info.get("formats"):
                    break
            except Exception as e:
                last_error = str(e)
                info = None
                continue

        if not info:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": last_error or "Could not extract video info with any client."
            }).encode())
            return

        raw_formats = info.get("formats", []) or [info]
        formats = []
        for f in raw_formats:
            formats.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution") or f.get("format_note") or "audio only",
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "filesize": f.get("filesize") or f.get("filesize_approx"),
                "note": f.get("format_note"),
            })

        build_headers(self)
        self.wfile.write(json.dumps({
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "formats": formats,
        }).encode())
        
