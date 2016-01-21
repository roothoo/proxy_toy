import SimpleHTTPServer
import BaseHTTPServer


class RequestHanler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_POST(self):
        length = self.headers.getheader('content-length')
        content_type = self.headers.getheader('content-type')
        nbytes = int(length)
        data = self.rfile.read(nbytes)

        print content_type
        print data

        self.wfile.write(data)


httpd = BaseHTTPServer.HTTPServer(('', 8000), RequestHanler)

httpd.serve_forever()