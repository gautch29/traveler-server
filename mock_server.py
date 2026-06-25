import http.server
import socketserver
import os
import re
import argparse
import hashlib

PORT = 8000

def get_flight_status(flight_code):
    flight_code = flight_code.replace(" ", "").upper()
    if not flight_code:
        flight_code = "UNKNOWN"
        
    h = hashlib.md5(flight_code.encode('utf-8')).hexdigest()
    val = int(h, 16)
    
    statuses = ["On Time", "On Time", "On Time", "Delayed", "Departed", "Arrived", "Boarding"]
    status = statuses[val % len(statuses)]
    
    delay_mins = 0
    if status == "Delayed":
        delay_mins = (val % 8 + 1) * 5
        
    gates = ["A12", "B22", "C10", "D45", "E11", "F28", "G3", "H19", "K35"]
    gate = gates[val % len(gates)]
    
    terminals = ["1", "2E", "2F", "3", "4", "A", "B", "C"]
    terminal = terminals[(val >> 2) % len(terminals)]
    
    aircrafts = ["Boeing 777-300ER", "Airbus A350-900", "Boeing 787-9 Dreamliner", "Airbus A330-900neo", "Boeing 737 MAX 9", "Airbus A321neo"]
    aircraft = aircrafts[(val >> 4) % len(aircrafts)]
    
    dep_city = "Paris (CDG)"
    arr_city = "New York (JFK)"
    
    if flight_code.startswith("AF"):
        dep_city = "Paris (CDG)"
        arr_city = "New York (JFK)" if val % 2 == 0 else "Los Angeles (LAX)"
    elif flight_code.startswith("DL"):
        dep_city = "New York (JFK)"
        arr_city = "Paris (CDG)" if val % 2 == 0 else "Atlanta (ATL)"
    elif flight_code.startswith("UA"):
        dep_city = "San Francisco (SFO)"
        arr_city = "Paris (CDG)" if val % 2 == 0 else "Chicago (ORD)"
    elif flight_code.startswith("AA"):
        dep_city = "Miami (MIA)"
        arr_city = "Paris (CDG)" if val % 2 == 0 else "Dallas (DFW)"
    elif flight_code.startswith("BF720"):
        dep_city = "Paris (ORY)"
        arr_city = "Newark (EWR)"
    elif flight_code.startswith("BF743"):
        dep_city = "Miami (MIA)"
        arr_city = "Paris (ORY)"
    elif flight_code.startswith("BF"):
        dep_city = "Paris (ORY)"
        arr_city = "Miami (MIA)" if val % 2 == 0 else "Newark (EWR)"
    elif flight_code.startswith("B62523") or flight_code.startswith("B6"):
        dep_city = "Washington (DCA)"
        arr_city = "Orlando (MCO)"
    else:
        cities = ["London (LHR)", "Rome (FCO)", "Madrid (MAD)", "Tokyo (HND)", "Dubai (DXB)", "San Francisco (SFO)", "Miami (MIA)", "Boston (BOS)"]
        dep_city = cities[val % len(cities)]
        arr_city = cities[(val + 1) % len(cities)]

    hour = (val % 12) + 1
    minute = (val % 4) * 15
    ampm = "AM" if (val % 2 == 0) else "PM"
    sched_time = f"{hour:02d}:{minute:02d} {ampm}"
    
    if delay_mins > 0:
        tot_mins = hour * 60 + minute + delay_mins
        est_hour = (tot_mins // 60)
        est_min = tot_mins % 60
        est_ampm = ampm
        if est_hour > 12:
            est_hour = est_hour % 12
            if est_hour == 0:
                est_hour = 12
        est_time = f"{est_hour:02d}:{est_min:02d} {est_ampm}"
    else:
        est_time = sched_time
        
    return {
        "flightNumber": flight_code,
        "status": status,
        "gate": gate,
        "terminal": terminal,
        "delayMinutes": delay_mins,
        "scheduledDeparture": sched_time,
        "estimatedDeparture": est_time,
        "aircraft": aircraft,
        "departureCity": dep_city,
        "arrivalCity": arr_city,
        "baggageClaim": str((val % 15) + 1)
    }

def generate_ai_summary(title, location_name, items):
    import random
    if not items:
        templates = [
            f"Enjoy a flexible day of free exploration in {location_name}. Discover the local scene, try regional dining, and relax at your own pace.",
            f"A free day in {location_name} to explore without a set schedule. Ideal for spontaneous discoveries and sightseeing.",
            f"Free exploration day in {location_name}. Take the time to wander, relax, and explore the city's hidden gems."
        ]
        return random.choice(templates)
        
    narratives = []
    
    # Start sentence
    first_item = items[0]
    first_title = first_item.get('title', 'activities')
    first_time = first_item.get('time', '')
    first_details = first_item.get('details', '')
    
    intro_templates = [
        f"Begin the day in {location_name} with {first_title} at {first_time} ({first_details}).",
        f"Kick off your morning in {location_name} experiencing {first_title} scheduled for {first_time}—{first_details}.",
        f"Your day in {location_name} starts at {first_time} with {first_title}, focusing on {first_details}."
    ]
    narratives.append(random.choice(intro_templates))
    
    # Middle sentences
    if len(items) > 2:
        for item in items[1:-1]:
            t = item.get('title', '')
            tm = item.get('time', '')
            d = item.get('details', '')
            mid_templates = [
                f"Next, head over to {t} at {tm} ({d}).",
                f"Following that, you'll join {t} around {tm}, which involves {d}.",
                f"Later at {tm}, transition to {t} ({d})."
            ]
            narratives.append(random.choice(mid_templates))
            
    # Final sentence
    if len(items) > 1:
        last_item = items[-1]
        last_title = last_item.get('title', '')
        last_time = last_item.get('time', '')
        last_details = last_item.get('details', '')
        outro_templates = [
            f"Conclude the evening with {last_title} at {last_time} ({last_details}).",
            f"Finally, wrap up your day with {last_title} scheduled at {last_time}—{last_details}.",
            f"End the day at {last_time} attending {last_title} ({last_details})."
        ]
        narratives.append(random.choice(outro_templates))
        
    return " ".join(narratives)

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
        if self.path.startswith('/flight-status'):
            import urllib.parse
            import json
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            flight_code = query_params.get('flight', [''])[0].strip().upper()
            if not flight_code:
                parts = parsed_url.path.strip('/').split('/')
                if len(parts) > 1:
                    flight_code = parts[1].strip().upper()
            
            status_data = get_flight_status(flight_code)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(status_data).encode('utf-8'))
            return

        if self.path != '/trip.json' and self.path != '/expenses.json':
            import urllib.parse
            url_path = self.path.lstrip('/')
            decoded_path = urllib.parse.unquote(url_path)
            
            # Check direct file or file in server/ folder (handles project root running)
            path_candidates = [decoded_path]
            if os.path.exists('server') and os.path.isdir('server'):
                path_candidates.append(os.path.join('server', decoded_path))
                
            found_path = None
            for cand in path_candidates:
                if os.path.exists(cand) and os.path.isfile(cand):
                    found_path = cand
                    break
                    
            if found_path:
                content_type = 'application/octet-stream'
                if found_path.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif found_path.endswith('.pkpass'):
                    content_type = 'application/vnd.apple.pkpass'
                elif found_path.endswith('.json'):
                    content_type = 'application/json'
                    
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-Length', str(os.path.getsize(found_path)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(found_path, 'rb') as f:
                    self.wfile.write(f.read())
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
            
        elif self.path == '/list-files':
            import json
            import glob
            files = []
            for prefix in ['', 'server/']:
                for folder in ['tickets', 'passes']:
                    pattern = os.path.join(prefix, folder, '*')
                    for path in glob.glob(pattern):
                        if os.path.isfile(path):
                            rel_path = os.path.relpath(path, prefix if prefix else '.')
                            if rel_path not in files:
                                files.append(rel_path)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode('utf-8'))
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
        if self.path.startswith('/flight-status'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return

        if self.path != '/trip.json' and self.path != '/expenses.json':
            import urllib.parse
            url_path = self.path.lstrip('/')
            decoded_path = urllib.parse.unquote(url_path)
            
            # Check direct file or file in server/ folder (handles project root running)
            path_candidates = [decoded_path]
            if os.path.exists('server') and os.path.isdir('server'):
                path_candidates.append(os.path.join('server', decoded_path))
                
            found_path = None
            for cand in path_candidates:
                if os.path.exists(cand) and os.path.isfile(cand):
                    found_path = cand
                    break
                    
            if found_path:
                content_type = 'application/octet-stream'
                if found_path.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif found_path.endswith('.pkpass'):
                    content_type = 'application/vnd.apple.pkpass'
                elif found_path.endswith('.json'):
                    content_type = 'application/json'
                    
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-Length', str(os.path.getsize(found_path)))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
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
            
        elif self.path == '/generate-summary':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                import json
                payload = json.loads(post_data.decode('utf-8'))
                title = payload.get('title', '')
                loc_name = payload.get('locationName', '')
                items = payload.get('items', [])
                
                summary = generate_ai_summary(title, loc_name, items)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"summary": summary}).encode('utf-8'))
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
