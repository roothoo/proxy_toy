# select just inputs
# inspired by :http://voorloopnul.com/blog/a-python-proxy-in-less-than-100-lines-of-code/

# 10061 is WSAECONNREFUSED, 'connection refused', which means either a firewall (unlikely) or more probably nothing listening at the IP:port you tried to connect to.
# socket.error: [Errno 10054] An existing connection was forcibly closed by the remote host
# [Errno 10035] The socket is non-blocking so recv() will raise an exception if there is no data to read. Note that errno.EWOULDBLOCK = errno.EAGAIN = 11. This is Python's (well the OS really) way of telling you to try the recv() again later.
import inspect
import socket
import errno
import select
import threading
import time
import re
import traceback

buffer_size = 4096
delay = 0.001


class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception, e:
            print e
            return False


class TheServer:
    input_list = []
    client_list = []
    client_channel = {}
    server_channel = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def print_status(self):
        while True:
            time.sleep(5)
            print 'input_list=',len(self.input_list), ' client_list=',len(self.client_list), \
                ' client_channel=',len(self.client_channel), ' server_channel=', len(self.server_channel)

    def main_loop(self):
        t = threading.Thread(target=self.print_status)
        t.start()

        self.input_list.append(self.server)
        while True:
            time.sleep(delay)
            inputready, outputready, exceptready = select.select(self.input_list, [], [])
            for s in inputready:
                if s == self.server:
                    self.on_accept()
                elif self.client_list.__contains__(s):
                    self.on_client_data(s)
                elif self.server_channel.__contains__(s):
                    self.on_server_data(s)
                else:
                    print 'neither client_channel nor server_channel'
                    s.close()
                    if s in self.input_list:
                        self.input_list.remove(s)

    def on_accept(self):
        clientsock, clientaddr = self.server.accept()
        print 'connected by ', clientaddr
        self.input_list.append(clientsock)
        self.client_list.append(clientsock)

    def on_client_data(self, clientsock):
        try:
            data = clientsock.recv(buffer_size)
        except socket.error, e:
            if e.args[0] == errno.ECONNRESET:
                print 'ECONNRESET'
            print e
            traceback.print_exc()
            return
        if data == '':
            # close clientsock and serverclient
            clientsock.close()
            self.input_list.remove(clientsock)
            self.client_list.remove(clientsock)
            if self.client_channel.__contains__(clientsock):
                serversock = self.client_channel[clientsock]
                del self.client_channel[clientsock]
                if self.server_channel.__contains__(serversock):
                    del self.server_channel[serversock]
                    if serversock in self.input_list:
                        self.input_list.remove(serversock)
            return

        try:
            if not self.client_channel.__contains__(clientsock):
                request = get_client_request(data)
                if request:
                    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    host = socket.gethostbyname(request.header['Host'])
                    port = 80
                    serversock.connect((host, port))
                    # serversock.setblocking(0)
                    self.client_channel[clientsock] = serversock
                    self.server_channel[serversock] = clientsock
                    if serversock not in self.input_list:
                        self.input_list.append(serversock)
                else:
                    return
            serversock = self.client_channel[clientsock]
            serversock.send(data)
        except Exception, e:
            print e
            traceback.print_exc()

    def on_server_data(self, serversock):
        clientsock = self.server_channel[serversock]
        data = serversock.recv(buffer_size)
        if data == '':
            # close serversock and clientsock
            serversock.close()
            self.input_list.remove(serversock)
            del self.server_channel[serversock]
            if clientsock:
                # clientsock.close()
                # self.client_list.remove(clientsock)
                del self.client_channel[clientsock]
            return
        if clientsock:
            try:
                clientsock.send(data)
            except socket.error, e:
                if e.args[0] == errno.WSAEWOULDBLOCK:
                    print 'WSAEWOULDBLOCK ', e
                print e
                traceback.print_exc()
        else:
            print 'server_channel[serversock] is None'

def print_error(e):
    message = 'Code location {0.filename}@{0.lineno}:'.format(inspect.getframeinfo(inspect.currentframe()))
    print 'e=', str(e)
    print message

class HTTPRequest(object):
    method = ''
    uri = ''
    version = ''
    header = None
    body = ''


def get_client_request(data):
    try:
        if data is None or data == '':
            return False
        request = HTTPRequest()
        headers = re.split('\r\n', re.split('\r\n\r\n', data)[0])
        # method
        first_line = re.split(' ', headers[0])
        request.method = first_line[0]
        request.uri = first_line[1]
        request.version = first_line[2]

        headers.pop(0)
        header_dict = {}
        for h in headers:
            param_key = re.split(':', h)[0]
            param_value = re.split(':', h)[1]
            param_key = param_key.strip()
            param_value = param_value.strip()
            header_dict[param_key] = param_value
        request.header = header_dict
        return request

    except Exception, e:
        print 'getClientRequest error = ' + str(e)
        print 'data = ' + data
        return False

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 8888
    proxy_sever = TheServer(host,  port)
    proxy_sever.main_loop()