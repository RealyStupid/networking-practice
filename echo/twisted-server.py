from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint

class Echo(Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        self.transport.write(f"Welcome! There are currently {self.factory.numProtocols} open connections.\n".encode('utf-8'))
        
    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols - 1

    def dataReceived(self, data):
        print(f'Client {self.factory.numProtocols} sent:', data.decode())
        self.transport.write(data)

class EchoFactory(Factory):
    def __init__(self):
        self.numProtocols = 0

    def buildProtocol(self, addr):
        print("Building protocol:", addr)
        return Echo(self)
    
if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, 8080)
    endpoint.listen(EchoFactory())
    reactor.run()