from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

# here we just feed the raw data back into the new file made!
class FileReceiver(Protocol):
    def connectionMade(self):
        print("Connected to server, receiving file...")
        self.output = open("sending_files/server_assets/received.jpg", "wb")

    def dataReceived(self, data):
        self.output.write(data)

    def connectionLost(self, reason):
        print("File received!")
        self.output.close()
        reactor.stop()

class FileClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        return FileReceiver()

reactor.connectTCP("127.0.0.1", 8080, FileClientFactory())
reactor.run()