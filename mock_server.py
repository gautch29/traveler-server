import http.server
import socketserver
import os
import re

PORT = 8000

class TravelerMockServer(http.server.SimpleHTTPRequestHandler):
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
            
        else:
            # Fallback to normal serving
            super().do_GET()

    def do_HEAD(self):
        if self.path == '/trip.json' or self.path.endswith('.pdf'):
            self.send_response(200)
            if self.path == '/trip.json':
                self.send_header('Content-type', 'application/json')
            else:
                self.send_header('Content-type', 'application/pdf')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        else:
            super().do_HEAD()

if __name__ == '__main__':
    # Make sure we run in the server directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    handler = TravelerMockServer
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Traveler Mock Server running at http://localhost:{PORT}")
        print("Serving trip.json and auto-generating mock PDFs on demand.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
