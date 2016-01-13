import json
import socket
import re

import nil as nil

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
    request = nil
    reqRawData = ''
    reqSock = nil
    reqConn = nil

    serverIp = ''
    serverPort = 80
    serverSock = nil
    serverData = ''

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


def doProxy(simpleProxy):
    reqRawData = simpleProxy.reqRawData
    reqConn = simpleProxy.reqConn
    serverSock = simpleProxy.serverSock

    serverSock.send(reqRawData)
    # recv data from server
    serverData = serverSock.recv(4096)
    if len(serverData) == 4096:
        while True:
            recvData = serverSock.recv(4096)
            if recvData == '':
                break
            serverData += recvData
    print serverData
    simpleProxy.serverData = serverData
    # send serverData to client
    reqConn.sendall(serverData)


def socket_server_test():
    try:
        clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = "127.0.0.1"
        port = 8888
        clientSock.bind((host, port))
        clientSock.listen(5)
        reqConn, addr = clientSock.accept()
        print "connected by ", addr

        simpleProxy = SimpleProxy()
        while True:
            reqRawData = reqConn.recv(4096)
            request = getClientRequest(reqRawData)

            print json.dumps(request.__dict__)
            hostName = request.header['Host']
            if simpleProxy.request == nil or cmp(hostName, simpleProxy.request.header['Host']) != 0:
                simpleProxy.serverIp = socket.gethostbyname(hostName)

            simpleProxy.reqRawData = reqRawData
            simpleProxy.request = request
            simpleProxy.reqSock = clientSock
            simpleProxy.reqConn = reqConn

            serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverSock.connect((simpleProxy.serverIp, simpleProxy.serverPort))
            simpleProxy.serverSock = serverSock

            doProxy(simpleProxy)

    except Exception, e:
        print e
    finally:
        if simpleProxy == nil:
            return
        if simpleProxy.reqConn != nil:
            simpleProxy.reqConn.close()
        if simpleProxy.reqSock != nil:
            simpleProxy.reqSock.close()
        if simpleProxy.serverSock != nil:
            simpleProxy.serverSock.close()