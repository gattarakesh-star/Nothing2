from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import yt_dlp


def build_headers(handler):
    handler.send_response(200)
    handler.send_header("Content-type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.end_headers()


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

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            # Uncomment and point to a cookies file if YouTube starts
            # blocking requests from Vercel's servers:
            # "cookiefile": "/tmp/cookies.txt",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

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

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
