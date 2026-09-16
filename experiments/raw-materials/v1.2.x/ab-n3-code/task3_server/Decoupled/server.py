#!/usr/bin/env python3
"""Static file HTTP server"""
import argparse, os, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

class H(SimpleHTTPRequestHandler):
    def log_message(self, f, *a):
        print(f"[{self.log_date_time_string()}] {f % a}")

def run(port, d):
    if not os.path.isdir(d):
        print(f"Error: dir {d} not found", file=sys.stderr); sys.exit(1)
    if not 1 <= port <= 65535:
        print(f"Error: invalid port {port}", file=sys.stderr); sys.exit(1)
    handler = lambda *a, **k: H(*a, directory=d, **k)
    srv = HTTPServer(("0.0.0.0", port), handler)
    print(f"Serving http://0.0.0.0:{port} from {os.path.abspath(d)}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped"); srv.server_close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", "--port", type=int, default=8000)
    p.add_argument("-d", "--dir", default=".")
    a = p.parse_args()
    run(a.port, a.dir)

if __name__ == "__main__":
    main()
