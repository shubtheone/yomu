import http.server
import socketserver
import json
import sys
from deep_translator import GoogleTranslator

PORT = 8000

class YomuHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/translate':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                text = data.get('text', '')
                if not text:
                    self.send_error(400, "Text is required")
                    return

                # Perform translation
                translator = GoogleTranslator(source='auto', target='en')
                translated = translator.translate(text)

                response = {'translation': translated}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"Translation error: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404)

    def do_GET(self):
        super().do_GET()

print(f"Starting Yomu server on port {PORT}...")
print("  - Serving static files")
print("  - API endpoint: POST /api/translate")

# Allow address reuse to avoid "Address already in use" errors on restart
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), YomuHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()
        sys.exit(0)
