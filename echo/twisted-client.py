from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

class EchoClient(Protocol):
    def connectionMade(self):
        print("Connected to server")
        msg = input("write an message: ")
        self.transport.write(msg.encode())

    def dataReceived(self, data):
        print("Server said:", data.decode())

    def connectionLost(self, reason):
        print("Connection lost")
        if reactor.running:
            reactor.stop()

class EchoClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        return EchoClient()

    def clientConnectionFailed(self, connector, reason):
        print("Connection failed:", reason)
        reactor.stop()

if __name__ == "__main__":
    reactor.connectTCP("127.0.0.1", 8080, EchoClientFactory())
    reactor.run()
