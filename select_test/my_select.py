import Queue
import re
import select
import socket
import sys

REQ_LEN = 4096
RES_LEN = 8096
inputs = []
outputs = []

clientMap = {}
serverMap = {}


def proxyLoop():
    listenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 8888
    listenSock.bind((host, port))
    listenSock.setblocking(0)
    listenSock.listen(5)
    inputs.append(listenSock)

    i = 0
    while True:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        i += 1
        if i % 10 == 0:
            print 'inputs=', len(inputs), ' outputs=', len(outputs), 'readable=',len(readable), 'writable=',len(writable), ' exceptional=', len(exceptional)
        for r in readable:
            if r is listenSock:
                clientConn, clientAddr = r.accept()
                clientConn.setblocking(0)
                print 'connected by ', clientAddr
                simpleProxy = SimpleProxy()
                simpleProxy.listenSock = listenSock
                simpleProxy.clientConn = clientConn
                simpleProxy.clientAddr = clientAddr
                clientMap[clientConn] = simpleProxy
                inputs.append(clientConn)
                outputs.append(clientConn)
            elif clientMap.__contains__(r):
                simpleProxy = clientMap[r]
                # clientConn ready
                data = r.recv(REQ_LEN)
                if data:
                    # request data ready
                    if simpleProxy.reqRawDataQ is None:
                        simpleProxy.reqRawDataQ = Queue.Queue()
                    reqRawDataQ = simpleProxy.reqRawDataQ
                    reqRawDataQ.put(data)
                    # get HTTP request
                    request = getClientRequest(data)
                    simpleProxy.request = request
                    if simpleProxy.serverSock is None:
                        # connet server sock
                        serverSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                        serverIp = socket.gethostbyname(request.header['Host'])
                        serverPort = 80
                        serverSock.connect((serverIp, serverPort))
                        serverSock.setblocking(0)
                        simpleProxy.serverSock = serverSock
                        simpleProxy.serverIp = serverIp
                        simpleProxy.serverPort = serverPort
                    else:
                        serverSock = simpleProxy.serverSock

                    if serverSock not in inputs:
                        inputs.append(serverSock)
                    if serverSock not in outputs:
                        outputs.append(serverSock)
                    serverMap[serverSock] = simpleProxy
                else:
                    # Interpret empty result as closed connection
                    closeClientServer(simpleProxy.clientConn, simpleProxy.listenSock)
            elif serverMap.__contains__(r):
                # resonse data ready
                simpleProxy = serverMap[r]

                data = r.recv(RES_LEN)
                if data:
                    if simpleProxy.serverDataQ is None:
                        simpleProxy.serverDataQ = Queue.Queue()
                    serverDataQ = simpleProxy.serverDataQ
                    serverDataQ.put_nowait(data)
                else:
                    print >>sys.stderr, 'resonse data empty'
                    closeClientServer(simpleProxy.clientConn, simpleProxy.serverSock)
            else:
                print >>sys.stderr, 'r is neither in clientMap nor serverMap'
                if r is listenSock:
                    continue
                if r in inputs:
                    inputs.remove(r)
                if r in outputs:
                    outputs.remove(r)

        for w in writable:
            if clientMap.__contains__(w):
                simpleProxy = clientMap[w]
                serverDataQ = simpleProxy.serverDataQ
                if serverDataQ is None or serverDataQ.empty():
                    continue
                data = serverDataQ.get_nowait()
                # send response data to client
                w.send(data)
            elif serverMap.__contains__(w):
                simpleProxy = serverMap[w]
                reqRawDataQ = simpleProxy.reqRawDataQ
                if reqRawDataQ is None or reqRawDataQ.empty():
                    continue
                data = reqRawDataQ.get_nowait()
                # send request data to server
                w.send(data)
            else:
                print >>sys.stderr, 'w is neither in clientMap nor serverMap'
                if w is listenSock:
                    continue
                if w in inputs:
                    inputs.remove(w)
                if w in outputs:
                    outputs.remove(w)
                pass


def closeClientServer(clientConn, serverSock):
    # Stop listening for input on the connection
    # close client sock; remove inputs,outputs; del serverMap
    if clientConn is not None:
        clientConn.close()
        if clientConn in inputs:
            inputs.remove(clientConn)
        if clientConn in outputs:
            outputs.remove(clientConn)
        if  clientMap.__contains__(clientConn):
            del clientMap[clientConn]
        if clientConn in inputs:
            inputs.remove(clientConn)
        if clientConn in outputs:
            outputs.remove(clientConn)

    # close server sock; remove inputs,outputs; del serverMap
    if serverSock is not None:
        serverSock.close()
        if serverSock in inputs:
            inputs.remove(serverSock)
        if serverSock in outputs:
            outputs.remove(serverSock)
        if serverMap.__contains__(serverSock):
            del serverMap[serverSock]
        if serverSock in inputs:
            inputs.remove(serverSock)
        if serverSock in outputs:
            outputs.remove(serverSock)


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
    reqRawDataQ = None
    listenSock = None
    clientConn = None
    clientAddr = None

    serverIp = ''
    serverPort = 80
    serverSock = None
    serverDataQ = None


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