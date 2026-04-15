import json
import logging
import mimetypes
import socket
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread, Event

BASE_DIR = Path(__file__).resolve().parent
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 3000
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000
BUFFER_SIZE = 1024
STORAGE_PATH = BASE_DIR / "storage" / "data.json"


stop_event = Event()


class HttpRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for pages and static assets."""

    def do_GET(self):
        # Routes GET requests to HTML pages or static files.
        route = urllib.parse.urlparse(self.path)

        match route.path:
            case "/":
                self.send_html(f"{BASE_DIR}/index.html")
            case "/message":
                self.send_html(f"{BASE_DIR}/message.html")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                print(file)
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html(f"{BASE_DIR}/error.html", 404)

    def do_POST(self):
        """Sends form payload to the UDP socket server and redirects to /message."""
        data_size = self.headers.get("Content-Length")
        data = self.rfile.read(int(data_size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header("Location", "/message")
        self.end_headers()

    def send_html(self, filename: str, status_code: int = 200) -> None:
        """Loads and returns HTML content with the given status code."""
        content = self.file_processing(filename)
        if content is None:
            return

        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(content)

    def send_static(self, filename, status_code=200) -> None:
        """Serves static files with MIME type detection."""
        content = self.file_processing(filename)
        if content is None:
            return

        self.send_response(status_code)

        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Contant-Type", mime_type)
        else:
            self.send_header("Contant-Type", "text/plain")

        self.end_headers()
        self.wfile.write(content)

    def file_processing(self, filename: str) -> bytes | None:
        """Reads file bytes and returns 404 if reading fails."""
        try:
            with open(filename, "rb") as file:
                content = file.read()
        except OSError as err:
            logging.error("Cannot read file %s: %s", filename, err)
            self.send_error(404, "File not found")
            return
        else:
            return content


def save_data_from_form(data: bytes) -> None:
    """Parses URL-encoded form data and saves it to JSON storage."""
    parse_data = urllib.parse.unquote(data.decode())

    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as file:
            parse_dict = json.load(file)

        parse_dict[str(datetime.now())] = {
            key: value for key, value in [el.split("=") for el in parse_data.split("&")]
        }

        with open(STORAGE_PATH, "w", encoding="utf-8") as file:
            json.dump(parse_dict, file, ensure_ascii=False, indent=4)

        logging.info("Message saved")
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging(err)


def run_http_server(http_server: HTTPServer):
    """Runs the HTTP server loop until shutdown."""
    logging.info("HTTP-server started")
    http_server.serve_forever(poll_interval=0.5)  # responds faster to shutdown()
    logging.info("HTTP-server stopped")


def run_socket_server(host: str, port: int, stop_event: Event) -> None:
    """Receives UDP messages from POST handler and persists form data."""
    socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_server.bind((host, port))
    socket_server.settimeout(0.5)  # so that the loop can check stop_event
    logging.info("Socket-server started")

    try:
        while not stop_event.is_set():
            try:
                data, address = socket_server.recvfrom(BUFFER_SIZE)
                save_data_from_form(data)
            except socket.timeout:
                continue
    finally:
        socket_server.close()
        logging.info("Socket-server stopped")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    storage = BASE_DIR / "storage"
    storage.mkdir(exist_ok=True)

    data_file = storage / "data.json"
    if not data_file.exists():
        with data_file.open("w", encoding="utf-8") as file:
            json.dump({}, file)

    http_server = HTTPServer((HTTP_HOST, HTTP_PORT), HttpRequestHandler)

    t_http = Thread(target=run_http_server, args=(http_server,), name="HTTP")
    t_sock = Thread(
        target=run_socket_server, args=("127.0.0.1", 5000, stop_event), name="SOCKET"
    )

    t_http.start()
    t_sock.start()

    """
        To allow stopping both the HTTP and socket servers with Ctrl+C, we use a shared Event.

        Because both servers run in worker threads, KeyboardInterrupt is handled in the main thread.
        When Ctrl+C is pressed, the main thread sets stop_event, and the worker threads check this flag and exit gracefully.
    """
    try:
        while True:
            stop_event.wait(1)
    except KeyboardInterrupt:
        logging.info("Servers shutdown")
        stop_event.set()
        http_server.shutdown()
        http_server.server_close()

    t_http.join()
    t_sock.join()
    logging.info("All stopped")
