import http.server
import socketserver
import os
from http import HTTPStatus
import subprocess
import fcntl
import time

PORT = int(os.getenv("PORT", 5123))
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 1))  # max request
TIME_WINDOW = int(os.getenv("TIME_WINDOW", 20))  # seconds
FULL_PATH_TO_GENERATE_USERNAME_SCRIPT = os.getenv(
    "FULL_PATH_TO_GENERATE_USERNAME_SCRIPT", "./generate-ide-username.sh"
)

# IP address -> last seen time.time()
request_log = {}

"""
Purpose in life:

Call generate-ide-username.sh , and respond immediately
with that username to the user (json response)

Queue (background task) the job of provisioning the IDE instance
by building an entire FIFO queueing infra (no, just append to a file for now).

So that the web client can poll (yes poll) until
their ide instance is online
https://karma-ide-<username>.ide.karmacomputing.co.uk
"""


class MyHandler(http.server.SimpleHTTPRequestHandler):

    def make_response(
        self, msg="", content_type="application/json", status=HTTPStatus.OK
    ):
        response = msg
        encoded = response.encode("utf-8", "surrogateescape")
        ctype = content_type
        self.send_response(status)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self, **kwargs):
        if self.path == "/new-username":
            client_ip = self.headers.get("x-forwarded-for")
            if client_ip is None:
                print(
                    "client_ip was None (no x-forwarded-for). Refusing to proceed"  # noqa: E501
                )  # noqa: E501
                return 255
            # Poor persons rate limitter
            now = time.time()
            if client_ip not in request_log:
                request_log[client_ip] = now
                print(f"Client IP {client_ip} added to request_log")
            # Remove timestamps older than TIME_WINDOW
            # We .copy to avoid
            # "RuntimeError: dictionary changed size during iteration"
            for key in request_log.copy().keys():
                if request_log[key] < now - TIME_WINDOW:
                    del request_log[key]
                    print("Deleted expired rate limit for {key}")
                if key in request_log and request_log[key] <= TIME_WINDOW:
                    print("rejecting request due to date limit")
                    self.make_response(
                        msg="Slow down buddy!",
                        status=HTTPStatus.TOO_MANY_REQUESTS,  # noqa: E501
                    )

            # Run schell script to generate username
            resp = subprocess.run(
                FULL_PATH_TO_GENERATE_USERNAME_SCRIPT, capture_output=True
            )  # noqa: E501
            username = resp.stdout.decode("utf-8").strip()
            response = f'{{"username": "{username}"}}'
            encoded = response.encode("utf-8", "surrogateescape")
            ctype = "application/json"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

            print(f"Writing username '{username}' to ide-creation-queue file")
            with open("../ide-creation-queue", "a") as fp:
                print("Attempting to aquire exclusive lock on file")
                # Remember, other consuming code needs to also test and
                # respect for the lock. There is no magic.
                # See https://docs.python.org/3/library/fcntl.html#fcntl.lockf
                fcntl.lockf(fp, fcntl.LOCK_EX)
                # Yes, we're explicitly stripping,
                # then re-adding and newline chars
                fp.write(f"{username}\n")
                print("Unlocking file descriptori on ide-creation-queue")

                fcntl.lockf(fp, fcntl.LOCK_UN)
                print("Append to ide-creation-queue complete")
        else:
            response = "Did you mean to hit /new-username?"
            encoded = response.encode("utf-8", "surrogateescape")
            ctype = "text/html"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            # We DONT want to serve dir index by default
            # super().do_GET(**kwargs)


Handler = MyHandler

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
