#!/usr/bin/env python3
"""静态文件HTTP服务器"""
import argparse
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

class StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=kwargs.pop("directory", os.getcwd()), **kwargs)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

def run(port, directory):
    if not os.path.isdir(directory):
        print(f"错误: 目录不存在 {directory}", file=sys.stderr)
        sys.exit(1)
    if not (1 <= port <= 65535):
        print(f"错误: 端口号无效 {port}", file=sys.stderr)
        sys.exit(1)
    handler = lambda *args, **kwargs: StaticHandler(*args, directory=directory, **kwargs)
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"静态文件服务器启动: http://0.0.0.0:{port}")
    print(f"服务目录: {os.path.abspath(directory)}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()

def main():
    parser = argparse.ArgumentParser(description="静态文件HTTP服务器")
    parser.add_argument("-p", "--port", type=int, default=8000, help="端口号（默认8000）")
    parser.add_argument("-d", "--directory", default=".", help="服务目录（默认当前目录）")
    args = parser.parse_args()
    run(args.port, args.directory)

if __name__ == "__main__":
    main()
