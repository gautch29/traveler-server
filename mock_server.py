import http.server
import socketserver
import os
import re
import ssl
import subprocess
import argparse

PORT = 8000
TOKEN = os.environ.get("TRAVELER_API_KEY", "traveler_secret_token_2026")

class TravelerMockServer(http.server.SimpleHTTPRequestHandler):
    def check_auth(self):
        auth_header = self.headers.get('Authorization')
        token_header = self.headers.get('X-Traveler-Token')
        
        expected_bearer = f"Bearer {TOKEN}"
        
        if auth_header == expected_bearer or token_header == TOKEN:
            return True
            
        # Send 401 Unauthorized
        self.send_response(401)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status": "error", "message": "Unauthorized: Missing or invalid token."}')
        return False

    def generate_minimal_pdf(self, title):
        # Escaping text for PDF
        clean_title = re.sub(r'[()]', '', title)
        # Construct PDF content
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
        if not self.check_auth():
            return
            
        # Route trip.json
        if self.path == '/trip.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                with open('trip.json', 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                # If run from root directory, check server/trip.json
                with open('server/trip.json', 'rb') as f:
                    self.wfile.write(f.read())
            return
            
        # Route any PDF request dynamically
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
            
        # Route any Wallet pass request dynamically
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
            # Fallback to normal serving
            super().do_GET()

    def do_HEAD(self):
        if not self.check_auth():
            return
            
        if self.path == '/trip.json' or self.path.endswith('.pdf') or self.path.endswith('.pkpass'):
            self.send_response(200)
            if self.path == '/trip.json':
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
        if not self.check_auth():
            return
            
        if self.path == '/trip.json':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                import json
                parsed_json = json.loads(post_data.decode('utf-8'))
                
                # Save locally
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
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    # Parse CLI Arguments
    parser = argparse.ArgumentParser(description="Traveler Mock Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--http", action="store_true", help="Run in HTTP mode (disable SSL)")
    parser.add_argument("--token", type=str, default=None, help="Authorization Bearer token")
    args = parser.parse_args()

    PORT = args.port
    if args.token:
        TOKEN = args.token

    # Make sure we run in the server directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if not args.http:
        cert_file = 'server.crt'
        key_file = 'server.key'
        
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            print("Generating self-signed SSL certificate...")
            try:
                subprocess.run([
                    'openssl', 'req', '-new', '-x509', '-keyout', key_file,
                    '-out', cert_file, '-days', '365', '-nodes',
                    '-subj', '/CN=localhost'
                ], check=True)
            except Exception as e:
                print(f"Error generating SSL certificate: {e}")
                
    handler = TravelerMockServer
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        if not args.http:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            print(f"Traveler Mock Server running at https://localhost:{PORT}")
            print("Serving trip.json and auto-generating mock PDFs on demand (HTTPS enabled).")
        else:
            print(f"Traveler Mock Server running at http://localhost:{PORT}")
            print("Serving trip.json and auto-generating mock PDFs on demand (HTTP mode).")
            
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
