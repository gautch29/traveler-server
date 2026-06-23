import http.server
import socketserver
import os
import re
import argparse

PORT = 8000

class TravelerMockServer(http.server.SimpleHTTPRequestHandler):
    def generate_minimal_pdf(self, title):
        clean_title = re.sub(r'[()]', '', title)
        content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>
endobj
5 0 obj
<< /Length 120 >>
stream
BT
/F1 18 Tf
50 700 Td
(TRAVELER APP DEMO TICKET) Tj
/F1 12 Tf
0 -40 Td
(Document: {clean_title}) Tj
0 -20 Td
(Status: Confirmed / Active) Tj
0 -20 Td
(Validity: July 2026) Tj
0 -40 Td
(Thank you for traveling with us! This is a mock ticket for testing.) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000228 00000 n 
0000000302 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
475
%%EOF
"""
        return content.encode('utf-8', errors='ignore')

    def do_GET(self):
        if self.path != '/trip.json' and self.path != '/expenses.json':
            import urllib.parse
            url_path = self.path.lstrip('/')
            decoded_path = urllib.parse.unquote(url_path)
            if decoded_path and os.path.exists(decoded_path) and os.path.isfile(decoded_path):
                super().do_GET()
                return

        if self.path == '/trip.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            target_path = 'trip.json' if os.path.exists('trip.json') else 'server/trip.json'
            with open(target_path, 'rb') as f:
                self.wfile.write(f.read())
            return
            
        elif self.path == '/expenses.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                target_path = 'expenses.json' if os.path.exists('expenses.json') else 'server/expenses.json'
                with open(target_path, 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.wfile.write(b'[]')
            return
            
        elif self.path.endswith('.pdf'):
            filename = os.path.basename(self.path)
            pdf_data = self.generate_minimal_pdf(filename)
            self.send_response(200)
            self.send_header('Content-type', 'application/pdf')
            self.send_header('Content-Length', str(len(pdf_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(pdf_data)
            return
            
        elif self.path.endswith('.pkpass'):
            pass_data = b"PKPASS_MOCK_BINARY_DATA"
            self.send_response(200)
            self.send_header('Content-type', 'application/vnd.apple.pkpass')
            self.send_header('Content-Length', str(len(pass_data)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(pass_data)
            return
            
        else:
            super().do_GET()

    def do_HEAD(self):
        if self.path != '/trip.json' and self.path != '/expenses.json':
            import urllib.parse
            url_path = self.path.lstrip('/')
            decoded_path = urllib.parse.unquote(url_path)
            if decoded_path and os.path.exists(decoded_path) and os.path.isfile(decoded_path):
                super().do_HEAD()
                return

        if self.path == '/trip.json' or self.path == '/expenses.json' or self.path.endswith('.pdf') or self.path.endswith('.pkpass'):
            self.send_response(200)
            if self.path == '/trip.json' or self.path == '/expenses.json':
                self.send_header('Content-type', 'application/json')
            elif self.path.endswith('.pdf'):
                self.send_header('Content-type', 'application/pdf')
            else:
                self.send_header('Content-type', 'application/vnd.apple.pkpass')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:
            super().do_HEAD()

    def do_POST(self):
        if self.path == '/trip.json':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                import json
                parsed_json = json.loads(post_data.decode('utf-8'))
                target_path = 'trip.json' if os.path.exists('trip.json') else 'server/trip.json'
                with open(target_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f'{{"status": "error", "message": "{str(e)}"}}'.encode('utf-8'))
            return
            
        elif self.path == '/expenses.json':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                import json
                parsed_json = json.loads(post_data.decode('utf-8'))
                target_path = 'expenses.json' if os.path.exists('expenses.json') else 'server/expenses.json'
                if not os.path.exists(target_path):
                    target_path = 'expenses.json'
                with open(target_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f'{{"status": "error", "message": "{str(e)}"}}'.encode('utf-8'))
            return
            
        elif self.path == '/upload':
            filename = self.headers.get('X-Filename')
            if not filename:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "Missing X-Filename header."}')
                return
                
            clean_filename = os.path.normpath(filename).lstrip('/')
            if clean_filename.startswith('..'):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "error", "message": "Invalid filename path."}')
                return
                
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                target_path = clean_filename
                if os.path.exists('server') and os.path.isdir('server'):
                    target_path = os.path.join('server', clean_filename)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'wb') as f:
                    f.write(post_data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f'{{"status": "error", "message": "{str(e)}"}}'.encode('utf-8'))
            return
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Traveler Mock Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()

    PORT = args.port
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    handler = TravelerMockServer
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Traveler Mock Server running at http://localhost:{PORT}")
        print("Serving trip.json and auto-generating mock PDFs on demand (HTTP mode).")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
