import http.server
import socketserver
import urllib.parse
import json
import os
import yt_dlp

PORT = int(os.environ.get("PORT", 8000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Keywords that indicate a "same-song variant" rather than a genuinely different song.
VERSION_KEYWORDS = [
    'remix', 'cover', 'karaoke', 'instrumental', 'slowed', 'reverb',
    '8d', 'nightcore', 'extended', 'edit', 'live', 'acoustic version',
    'sped up', 'speed up', 'lofi version', 'reprise', 'mashup',
]


def is_version_like(title):
    """Return True if the title looks like a variant of an existing song."""
    if not title:
        return False
    t = title.lower()
    return any(kw in t for kw in VERSION_KEYWORDS)


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if path == '/api/ping' or path == '/api/health':
            self.send_json_response({'status': 'ok', 'message': 'server is active'})
        elif path == '/api/search':
            self.handle_search(query_params)
        elif path == '/api/related':
            self.handle_related(query_params)
        elif path == '/':
            self.send_json_response({
                'status': 'ok',
                'service': 'youtube-custom-player-backend',
                'endpoints': ['/api/ping', '/api/search?q=...', '/api/related?title=...&id=...']
            })
        else:
            self.send_json_response({'error': 'not found'}, status=404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_search(self, params):
        q = params.get('q', [''])[0]
        if not q:
            self.send_json_response([])
            return

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch10',
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_query = q if q.startswith(('http://', 'https://')) else f"ytsearch10:{q}"
                res = ydl.extract_info(search_query, download=False)

                results = []
                entries = res.get('entries', [res]) if 'entries' in res or 'id' in res else []

                for entry in entries:
                    if entry:
                        video_id = entry.get('id')
                        if not video_id:
                            continue

                        title = entry.get('title') or 'Unknown Title'
                        uploader = entry.get('uploader') or entry.get('channel') or 'YouTube'
                        duration = entry.get('duration')
                        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                        results.append({
                            'id': video_id,
                            'title': title,
                            'uploader': uploader,
                            'duration': duration,
                            'thumbnail': thumbnail
                        })
                self.send_json_response(results)
        except Exception as e:
            print(f"Search error: {e}")
            self.send_json_response([], status=200)

    def handle_related(self, params):
        title = params.get('title', [''])[0]
        video_id = params.get('id', [''])[0]
        uploader = params.get('uploader', [''])[0]

        # ---- Attempt 1: YouTube Mix radio playlist (uses YT's own recs) ----
        if video_id:
            results = self._try_radio_mix(video_id)
            if results:
                self.send_json_response(results)
                return

        # ---- Attempt 2: Filtered search fallback ----
        if uploader:
            search_query = f"{uploader} similar songs -cover -remix -karaoke -slowed"
        elif title:
            search_query = f"{title} mix -cover -remix -karaoke -slowed -instrumental"
        else:
            search_query = "top hindi drive songs"

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch15',
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(f"ytsearch15:{search_query}", download=False)
                results = []
                for entry in res.get('entries', []):
                    if not entry:
                        continue
                    v_id = entry.get('id')
                    if not v_id or v_id == video_id:
                        continue
                    entry_title = entry.get('title') or ''
                    if is_version_like(entry_title):
                        continue
                    results.append({
                        'id': v_id,
                        'title': entry_title,
                        'uploader': entry.get('uploader') or entry.get('channel') or 'YouTube',
                        'thumbnail': f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                    })
                    if len(results) >= 8:
                        break

                # If filtering removed everything, fall back to unfiltered results
                if not results:
                    for entry in res.get('entries', []):
                        if entry and entry.get('id') and entry.get('id') != video_id:
                            v_id = entry['id']
                            results.append({
                                'id': v_id,
                                'title': entry.get('title'),
                                'uploader': entry.get('uploader') or entry.get('channel') or 'YouTube',
                                'thumbnail': f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                            })
                            if len(results) >= 6:
                                break

                self.send_json_response(results)
        except Exception as e:
            print(f"Related error: {e}")
            self.send_json_response({'error': str(e)}, status=500)

    def _try_radio_mix(self, video_id):
        """Fetch YouTube's own radio/mix playlist for the given video."""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'playlistend': 12,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                radio_url = f"https://www.youtube.com/playlist?list=RDAMVM{video_id}"
                res = ydl.extract_info(radio_url, download=False)
                entries = res.get('entries') or []

                # Need at least a few real entries; the first entry is usually
                # the seed video itself, so skip it.
                if len(entries) < 3:
                    return []

                results = []
                for entry in entries:
                    if not entry:
                        continue
                    v_id = entry.get('id')
                    if not v_id or v_id == video_id:
                        continue
                    entry_title = entry.get('title') or ''
                    if is_version_like(entry_title):
                        continue
                    results.append({
                        'id': v_id,
                        'title': entry_title,
                        'uploader': entry.get('uploader') or entry.get('channel') or 'YouTube',
                        'thumbnail': f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                    })
                    if len(results) >= 8:
                        break

                return results
        except Exception as e:
            print(f"Radio mix failed for {video_id}: {e}")
            return []

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Backend API running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")