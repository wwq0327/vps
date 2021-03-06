#coding:utf-8
from conf import  SAAS_PORT, SSL_CERT

from zkit.ip import address_to_in6
import thrift
from thrift.transport.TSocket import TSocket
from thrift.transport.TSSLSocket import TSSLServerSocket
from thrift.transport.TSocket import TServerSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer, TNonblockingServer
import threading
import logging
import select
import socket

import ssl

class MySSLServerSocket (TSSLServerSocket):
    """ change to raise ssl exception """

    allowed_ips = None

    def __init__ (self, host=None, port=9090, certfile='cert.pem', unix_socket=None, allowed_ips=None):
        assert allowed_ips is None or isinstance (allowed_ips, (list,set,tuple))
        TSSLServerSocket.__init__(self, host, port, certfile=certfile, unix_socket=unix_socket)
        if allowed_ips: 
            res = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE | socket.AI_ADDRCONFIG)
            af = res[-1][0]
            if socket.has_ipv6 and af == socket.AF_INET6:
                self.allowed_ips = map (lambda x: socket.inet_ntop (socket.AF_INET6, address_to_in6(x)), allowed_ips)
            else:
                self.allowed_ips = allowed_ips

    def accept(self):
        while True:
            plain_client, addr = self.handle.accept()
            #print self.allowed_ips, addr[0]
            if self.allowed_ips and addr[0] not in self.allowed_ips:
                logging.warn ("client %s is not allowed to connect" % (addr[0]))
                plain_client.close()
                continue

            try:
                client = ssl.wrap_socket(plain_client, certfile=self.certfile,
                              server_side=True, ssl_version=self.SSL_VERSION)
            except (ssl.SSLError), e:
              # failed handshake/ssl wrap, close socket to client
                plain_client.close()
                logging.exception (e)
                continue

            result = TSocket()
            result.setHandle(client)
            
            return result


def server(saas, handler, host=None, port=SAAS_PORT, allowed_ips=None):
    processor = saas.Processor(handler)
#    transport = TServerSocket(host, port=SAAS_PORT)
#    transport = TSSLServerSocket(host, port=SAAS_PORT, certfile=SSL_CERT)
    sock = MySSLServerSocket(host, port=port, certfile=SSL_CERT, allowed_ips=allowed_ips)
    #tfactory  = TTransport.TBufferedTransportFactory()
    tfactory  = TTransport.TFramedTransportFactory()
    pfactory  = TBinaryProtocol.TBinaryProtocolFactory()


    #server    = TServer.TSimpleServer(processor, sock, tfactory, pfactory)  # which cannot deal with exception correctly
    server = TServer.TThreadedServer(processor, sock, tfactory, pfactory)
    #server = TServer.TThreadPoolServer(processor, sock, tfactory, pfactory) # which will hang and only be kill by signal 9
    server.serve()


#def get_server_nonblock (saas, handler, host=None, allowed_ips=None):
    # which cannot work
#    processor = saas.Processor(handler)
#    socket = MySSLServerSocket(host, port=SAAS_PORT, certfile=SSL_CERT, allowed_ips=allowed_ips)
##    tfactory  = TTransport.TFramedTransportFactory()
##    pfactory  = TBinaryProtocol.TBinaryProtocolFactory()
#    server    = TNonblockingServer.TNonblockingServer (processor, socket)
#    return server

