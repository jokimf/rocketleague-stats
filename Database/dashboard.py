import queries as q
from http.server import BaseHTTPRequestHandler, HTTPServer

q.init()
hostName = "localhost"
serverPort = 8080
json = retrieveData()


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(json))


if __name__ == '__main__':
    webServer = HTTPServer((hostName, serverPort), MyServer)

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        print('ja')
    webServer.server_close()


def retrieveData():
    # TODO: Make master JSON to be fetched by JS
    pass
