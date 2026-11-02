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
        else:
            super().do_GET()

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
                # If it's a URL, use it directly, otherwise use ytsearch
                search_query = q if q.startswith(('http://', 'https://')) else f"ytsearch10:{q}"
                res = ydl.extract_info(search_query, download=False)
                
                results = []
                # Handle both single video and search results
                entries = res.get('entries', [res]) if 'entries' in res or 'id' in res else []
                
                for entry in entries:
                    if entry:
                        video_id = entry.get('id')
                        if not video_id: continue
                        
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
            self.send_json_response([], status=200) # Return empty list on error to avoid frontend crash

    def handle_related(self, params):
        title = params.get('title', [''])[0]
        video_id = params.get('id', [''])[0]
        
        # Search for related music tracks using song title + recommendations
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

if __name__ == '__main__':
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
