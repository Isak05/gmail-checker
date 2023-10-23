import argparse
import os
import json
import requests
import time
import math
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

host = ""
port = 0
client_id = ""
client_secret = ""
access_token = ""
refresh_token = ""
last_checked = 1
server_running = False


def open_oauth_window():
    print("Opening oauth in browser")
    webbrowser.open_new(
        "https://accounts.google.com/o/oauth2/v2/auth?client_id="
        + client_id
        + "&response_type=code&redirect_uri="
        + host
        + ":"
        + str(port)
        + "&scope=https://www.googleapis.com/auth/gmail.readonly"
    )
    run(addr=host, port=port)


def refresh_access_token():
    global client_id
    global client_secret
    global access_token
    global refresh_token

    print("Refreshing access token")

    x = requests.post(
        "https://oauth2.googleapis.com/token?client_id="
        + client_id
        + "&client_secret="
        + client_secret
        + "&grant_type=refresh_token&refresh_token="
        + refresh_token
    )
    if x.status_code != 200:
        access_token = ""
        print("Failed to refresh access token")
        open_oauth_window()
        return

    data = json.loads(x.text)
    file = open("tokens.dat", "r")
    a = file.readlines()
    file.close()
    file = open("tokens.dat", "w")
    if len(a) <= 0:
        a.append("")
    a[0] = data["access_token"] + "\n"
    file.writelines(a)
    access_token = data["access_token"]
    print("Successfully refreshed access token")


def poll_mail():
    global access_token
    global last_checked

    print("Polling Gmail")
    new_last_checked = math.floor(time.time())
    req = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?access_token="
        + access_token
        + "&q=is:unread after:"
        + str(last_checked)
        + "&maxResults=500"
    )
    print("Gmail response status code: " + str(req.status_code))
    if req.status_code != 200:
        return req

    last_checked = new_last_checked

    file = open("last-checked.dat", "w")
    file.write(str(last_checked))
    file.close()

    return req


def getNumNewMail():
    global access_token
    global last_checked

    req = poll_mail()

    if req.status_code == 401:
        ref = refresh_access_token()
        if access_token == "":
            return -1
        req = poll_mail()

    data = json.loads(req.text)

    try:
        num = len(data["messages"])
    except:
        num = 0

    return num


class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _html(self, message):
        content = f"<html><body><h2>{message}</h1></body></html>"
        return content.encode("utf8")

    def redirect_to_oauth(self):
        print("Redirecting to oauth page")
        self.send_response(302)
        self.send_header(
            "Location",
            "https://accounts.google.com/o/oauth2/v2/auth?client_id="
            + client_id
            + "&response_type=code&redirect_uri="
            + host
            + ":"
            + str(port)
            + "&scope=https://www.googleapis.com/auth/gmail.readonly",
        )
        self.end_headers()

    def do_GET(self):
        global client_id
        global client_secret
        global access_token
        global refresh_token
        global server_running

        parsed_path = urlparse(self.path)
        query_components = parse_qs(parsed_path.query)
        if "code" in query_components:
            code = query_components["code"][0]
            self._set_headers()
            x = requests.post(
                "https://oauth2.googleapis.com/token?client_id="
                + client_id
                + "&client_secret="
                + client_secret
                + "&grant_type=authorization_code&code="
                + code
                + "&redirect_uri="
                + host
                + ":"
                + str(port)
            )
            if x.status_code != 200:
                print("Couldn't retrieve access token")
                self.wfile.write(self._html("Authentication failed."))
                return
            data = json.loads(x.text)
            access_token = data["access_token"]
            refresh_token = data["refresh_token"]

            if access_token != "" and refresh_token != "":
                file = open("tokens.dat", "w+")
                a = file.readlines()
                if len(a) <= 1:
                    a.append("")
                    a.append("")
                a[0] = access_token + "\n"
                a[1] = refresh_token + "\n"
                file.writelines(a)
                file.close()

        if parsed_path.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        if access_token != "":
            self._set_headers()
            self.wfile.write(
                self._html("Authentication succeeded. You may now close this window.")
            )
            print("Retrieved access token")

        server_running = False

    def do_HEAD(self):
        self._set_headers()


def run(server_class=HTTPServer, handler_class=S, addr="localhost", port=8080):
    global server_running

    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    print(f"Starting httpd server on {addr}:{port}")
    server_running = True
    while server_running:
        httpd.handle_request()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-host",
        default="http://127.0.0.1",
    )
    parser.add_argument(
        "-port",
        type=int,
        default=8080,
    )
    parser.add_argument("-client_id")
    parser.add_argument("-client_secret")
    parser.add_argument("-audio_file")
    args = parser.parse_args()

    client_id = args.client_id
    client_secret = args.client_secret
    host = args.host
    port = args.port

    try:
        file = open("tokens.dat", "r")

        a = file.readlines()
        if len(a) >= 2:
            print("Reading tokens")
            access_token = a[0]
            refresh_token = a[1]
        file.close()
    except:
        pass

    try:
        file = open("last-checked.dat", "r")
        last_checked = int(file.read())
        file.close()
    except:
        pass

    if access_token == "":
        open_oauth_window()

    num = getNumNewMail()
    if num > 0:
        print("Sending notification")
        os.system(
            'notify-send "You\'ve got mail!" "'
            + str(min(499, num))
            + ("+" if num >= 500 else "")
            + " unread message"
            + ("s" if num > 1 else "")
            + '" --hint="string:desktop-entry:org.kde.konsole" --app-name="Gmail checker" -t 10000'
        )
        if args.audio_file != None and args.audio_file != "":
            print("Playing audio")
            os.system(
                "ffplay -nodisp -nostats -hide_banner -autoexit -volume 30 " + args.audio_file
            )
