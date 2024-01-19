import socketserver
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from typing import Union

import cv2
from PIL import Image

from config.config import ConfigStore


class StreamServer:
    """Interface for outputing camera frames."""

    def start(self, config_store: ConfigStore) -> None:
        """Starts the output stream."""
        raise NotImplementedError

    def set_frame(self, frame: cv2.Mat) -> None:
        """Sets the frame to serve."""
        raise NotImplementedError


class MjpegServer(StreamServer):
    _frame: cv2.Mat
    _has_frame: bool = False
    _fps: float = 0.0
    _latency: int = 0
    _last_served_timestamp: float = 0.0

    def _make_handler(self_mjpeg):  # type: ignore
        class StreamingHandler(BaseHTTPRequestHandler):
            HTML = """
    <html>
        <head>
            <title>Cubstar Debug</title>
            <style>
                body {
                    background-color: black;
                }

                img {
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    transform: translate(-50%, -50%);
                    max-width: 100%;
                    max-height: 100%;
                }
            </style>
        </head>
        <body>
            <img src="stream.mjpg" />
        </body>
    </html>
            """

            def do_GET(self):
                if self.path == "/":
                    content = self.HTML.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                elif self.path == "/stream.mjpg":
                    self.send_response(200)
                    self.send_header("Age", "0")
                    self.send_header("Cache-Control", "no-cache, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
                    self.end_headers()
                    try:
                        while True:
                            if not self_mjpeg._has_frame:
                                time.sleep(0.1)
                            else:
                                timestamp = time.time()
                                frame = self_mjpeg._frame.copy()
                                cv2.putText(frame, f"FPS: {self_mjpeg._fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                cv2.putText(frame, f"Latency: {self_mjpeg._latency}ms", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                cv2.putText(frame, f"Stream FPS: {(1 / (timestamp - self_mjpeg._last_served_timestamp)):.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                self_mjpeg._last_served_timestamp = timestamp

                                pil_im = Image.fromarray(frame)
                                stream = BytesIO()
                                pil_im.save(stream, format="JPEG")
                                frame_data = stream.getvalue()

                                self.wfile.write(b"--FRAME\r\n")
                                self.send_header("Content-Type", "image/jpeg")
                                self.send_header("Content-Length", str(len(frame_data)))
                                self.end_headers()
                                self.wfile.write(frame_data)
                                self.wfile.write(b"\r\n")

                    except Exception as e:
                        print("Removed streaming client %s: %s", self.client_address, str(e))
                else:
                    self.send_error(404)
                    self.end_headers()

        return StreamingHandler

    class StreamingServer(socketserver.ThreadingMixIn, HTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    def _run(self, port: int) -> None:
        server = self.StreamingServer(("", port), self._make_handler())
        server.serve_forever()

    def start(self, config_store: ConfigStore) -> None:
        threading.Thread(target=self._run, daemon=True, args=(config_store.local_config.stream_port,)).start()

    def set_frame(self, frame: cv2.Mat, fps: Union[float, None], latency: Union[int, None]) -> None:
        if fps != None:
            self._fps = fps
        if latency != None:
            self._latency = latency
        self._frame = frame
        self._has_frame = True
