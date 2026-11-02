import http.server
import socketserver
import urllib.parse
import json
import os
import yt_dlp

PORT = int(os.environ.get("PORT", 8000))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


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
            # Backend no longer serves the frontend; just confirm it's alive.
            self.send_json_response({
                'status': 'ok',
                'service': 'youtube-custom-player-backend',
                'endpoints': ['/api/ping', '/api/search?q=...', '/api/related?title=...&id=...']
            })
        else:
            self.send_json_response({'error': 'not found'}, status=404)

    def do_OPTIONS(self):
        # CORS preflight support
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

        search_query = f"{title} related songs" if title else "top hindi drive songs"

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch6',
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(f"ytsearch6:{search_query}", download=False)
                results = []
                for entry in res.get('entries', []):
                    if entry and entry.get('id') != video_id:
                        v_id = entry.get('id')
                        results.append({
                            'id': v_id,
                            'title': entry.get('title'),
                            'uploader': entry.get('uploader') or entry.get('channel') or 'YouTube',
                            'thumbnail': f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                        })
                self.send_json_response(results)
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        # Keep Render logs clean; remove if you want verbose access logs.
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