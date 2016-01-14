import json
import socket
import re
import threading

METHOD = ("GET", "POST", "UNKOWN")


class HTTPRequest(object):
    method = ''
    uri = ''
    version = ''
    header = None
    body = ''


class HTTPResponse(object):
    pass


class SimpleProxy(object):
    request = None
    reqRawData = ''
    reqSock = None
    reqConn = None

    serverIp = ''
    serverPort = 80
    serverSock = None
    serverData = ''

def getClientRequest(data):
    try:
        if data == None or data == '':
            return None
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


def doProxy(simpleProxy):
    reqRawData = simpleProxy.reqRawData
    reqConn = simpleProxy.reqConn
    serverSock = simpleProxy.serverSock

    serverSock.send(reqRawData)
    # recv data from server
    LEN = 4096 * 8
    serverData = serverSock.recv(LEN)
    if len(serverData) == LEN:
        while True:
            recvData = serverSock.recv(LEN)
            if recvData == '':
                break
            serverData += recvData
    # print serverData
    simpleProxy.serverData = serverData
    # send serverData to client
    reqConn.sendall(serverData)


def proxyLoop(reqSock, reqConn, addr):
    try:
        print 'thread %s is running...' % threading.currentThread().name
        simpleProxy = SimpleProxy()
        while True:
            print 'waiting for request'
            reqRawData = reqConn.recv(4096)
            request = getClientRequest(reqRawData)

            # print json.dumps(request.__dict__)
            print request.uri
            hostName = request.header['Host']
            if simpleProxy.request is None or cmp(hostName, simpleProxy.request.header['Host']) != 0:
                simpleProxy.serverIp = socket.gethostbyname(hostName)

            simpleProxy.reqRawData = reqRawData
            simpleProxy.request = request
            simpleProxy.reqSock = reqSock
            simpleProxy.reqConn = reqConn

            # socket.setdefaulttimeout(40)
            if simpleProxy.serverSock is None:
                serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                serverSock.connect((simpleProxy.serverIp, simpleProxy.serverPort))
                simpleProxy.serverSock = serverSock

            doProxy(simpleProxy)
    except Exception, e:
        print e


def socket_server_test():
    try:
        reqSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = "127.0.0.1"
        port = 8888
        reqSock.bind((host, port))
        reqSock.listen(10)

        threadList = []
        i = 0
        while True:
            reqConn, addr = reqSock.accept()
            print "connected by ", addr
            i += 1
            t = threading.Thread(target=proxyLoop, args=(reqSock, reqConn, addr), name="proxyLoop" + str(i))
            threadList.append(t)
            t.start()


    except Exception, e:
        print e
