# Video Quality Checker

Paste a video URL, get a list of every available quality/format via yt-dlp.

## Structure
- `public/index.html` — static frontend (input bar + results table)
- `api/formats.py` — Python serverless function, runs yt-dlp and returns JSON
- `requirements.txt` — tells Vercel to install `yt-dlp` for the Python function
- `vercel.json` — bumps the function timeout to 30s (yt-dlp extraction isn't instant)

## Local test (optional, needs Python 3.9+)
```bash
pip install yt-dlp
python -m http.server 3000 --directory public
# in another terminal, test the extraction logic directly:
python -c "import yt_dlp; yt_dlp.YoutubeDL({'skip_download': True}).extract_info('PASTE_URL', download=False)"
```
Vercel's local emulator (`vercel dev`) is the easiest way to test the actual `/api/formats` route end-to-end — install with `npm i -g vercel`, then run `vercel dev` in this folder.

## Deploy to Vercel
1. Push this folder to a GitHub repo.
2. Go to vercel.com → New Project → import the repo.
3. Vercel auto-detects `api/formats.py` as a Python function and serves `public/` statically. No build command needed — leave build settings default/empty.
4. Deploy.

## Known limitation: YouTube blocking
YouTube frequently blocks requests coming from datacenter IP ranges (which includes Vercel's), returning errors like "Sign in to confirm you're not a bot." This isn't a bug in this code — it happens to most yt-dlp-on-serverless setups. Workarounds, roughly in order of reliability:
- Export cookies from a logged-in YouTube session (e.g. with the "Get cookies.txt" browser extension) and pass `cookiefile` in `ydl_opts` in `api/formats.py`.
- Route requests through a residential/rotating proxy (set `proxy` in `ydl_opts`).
- Test first with non-YouTube sources (Vimeo, direct MP4 links, etc.) — those generally work without any of this.

## Extending
- To actually download instead of just listing formats, you'd need a different hosting approach — Vercel's serverless functions have short execution limits and no persistent disk, which makes large video downloads impractical there.
