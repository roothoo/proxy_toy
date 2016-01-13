import json
import socket
import re

from objc import nil

METHOD = ("GET", "POST", "UNKOWN")


class HTTPRequest(object):
    method = ''
    uri = ''
    version = ''
    header = nil
    body = ''


class HTTPResponse(object):
    pass


class SimpleProxy(object):
    request = HTTPRequest()
    reqSock = nil


def getClientRequest(data):
    try:
        if data == nil or data == '':
            return nil
        request = HTTPRequest()
        headers = re.split('\r\n', re.split('\r\n\r\n', data)[0])
        #method
        firstLine = re.split(' ', headers[0])
        request.method = firstLine[0]
        request.uri = firstLine[1]
        request.version = firstLine[2]

        headers.pop(0)
        headerDict = {}
        for h in headers:
            paramKey = re.split(':', h)[0]
            paramValue = re.split(':', h)[1]
            paramKey = paramKey.strip()
            paramValue = paramValue.strip()
            headerDict[paramKey] = paramValue
        request.header = headerDict
        return request

    except Exception, e:
        print 'getClientRequest error = ' + str(e)
        print 'data = ' + data


def socket_server_test():
    clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 8888
    clientSock.bind((host, port))
    clientSock.listen(5)

    oneProxy = SimpleProxy()
    oneProxy.reqSock = clientSock

    conn, addr = clientSock.accept()
    print "connected by ", addr

    try:
        data = conn.recv(4096)
        request = getClientRequest(data)
        simpleProxy = SimpleProxy()
        simpleProxy.request = request
        simpleProxy.reqSock = clientSock
        print json.dumps(request.__dict__)

        hostName = request.header['Host']
        serverIp = socket.gethostbyname(hostName)
        serverPort = 80
        serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSock.connect((serverIp, serverPort))
        serverSock.send(data)
        serverData = serverSock.recv(4096)
        # while True:
        #     recvData = serverSock.recv(1024)
        #     if recvData == '':
        #         break
        #     serverData += recvData
        print serverData
        conn.sendall(serverData)

    except Exception, e:
        print e
    finally:
        if conn != nil:
            conn.close()
        if clientSock != nil:
            clientSock.close()