from wsgiref.simple_server import make_server, demo_app


def application(environ, start_response):
    path = environ.get('PATH_INFO')
    if path == '/':
        response_body = 'Index'
    else:
        response_body = 'Hello'
    status = '200 OK'
    response_headers = [('Content-Length', str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]


host = '127.0.0.1'
port = 8000
httpd = make_server(host, port, application)
sa = httpd.socket.getsockname()
print 'connected at {0}:{1} '.format(*sa)
httpd.serve_forever()