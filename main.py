import json
import mimetypes
import os
import pathlib
import socket
import urllib.parse

from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from os import path
from threading import Thread
from time import sleep


IP = "127.0.0.1"
HTTP_PORT = 3000
UDP_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parse = urllib.parse.unquote_plus(data.decode())
        data_dict = {key: value for key, value in [el.split("=") for el in data_parse.split("&")]}
        sckt_server = Thread(target=socket_server)
        sckt_server.start()
        encode_data = json.dumps(data_dict, indent=2).encode("utf-8")
        sckt_client(encode_data)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


def socket_server():
    print("Socket is open")
    fpath = r".\storage\data.json"
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sckt.bind((IP, UDP_PORT))
    while True:
        global_dict = {}
        data, _ = sckt.recvfrom(1024)
        decode_data = json.loads(data)
        today = datetime.now()
        date_time = today.strftime(r"%Y-%m-%d %H:%M:%S")

        check_file = os.path.getsize(fpath)
        if check_file != 0:
            with open(fpath, "r") as jfile:
                readed = json.load(jfile)
            readed[date_time] = decode_data
            for_file = json.dumps(readed, indent=2)
        else:
            global_dict[date_time] = decode_data
            for_file = json.dumps(global_dict, indent=2)
        with open(fpath, "w") as jfile:
            jfile.write(for_file)
        print("Data saved to file")
        sleep(0.5)
        break
    print("Socket was closed.")
    sckt.close()


def sckt_client(incoming_data):
    sckt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sckt.sendto(incoming_data, (IP, UDP_PORT))
    sckt.close()


def run():
    server_address = (IP, HTTP_PORT)
    http = HTTPServer(server_address, HttpHandler)
    http_server = Thread(target=http.serve_forever)
    http_server.start()

    user_input = input('Press "Enter" to stop HTTP server\n')
    if not user_input:
        http.shutdown()


if __name__ == "__main__":
    run()
