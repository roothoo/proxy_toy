import socket
import re

METHOD = ("GET", "POST")


class HTTPHeader(object):
    params = {}


class HTTPRequest(object):
    method = METHOD[0]
    uri = ''
    version = '1.1'
    header = HTTPHeader()


class HTTPResponse(object):
    pass


class SimpleProxy(object):
    request = HTTPRequest()


def socket_server_test():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 8888
    s.bind((host, port))
    s.listen(5)

    conn, addr = s.accept()
    while True:
        print "connected by ", addr
        data = conn.recv(1024*4)

        headers = re.split('\r\n', re.split('\r\n\r\n', data)[0])

        if re.split('GET', headers[0])
        for h in headers:


        if not data:
            break
        reply = 'reply:' + data
        print data
        conn.sendall(reply)
    conn.close()
    s.close()