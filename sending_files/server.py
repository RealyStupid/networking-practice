from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

# To not overload the reactor by sending too much data
# sending the file in chunks allows us to make sure the reactor stays intact
CHUNK_SIZE = 4096

# Since twisted sends info via bytes we dont need to encrypt or decrypt anything!
class FileSender(Protocol):
    def connectionMade(self):
        print("Client connected")

        # open the file, make sure its in bianary mode
        self.file = open("sending_files/server_assets/content.png", "rb")

        self.sendChunk()

    def sendChunk(self):
        chunk = self.file.read(CHUNK_SIZE)

        if chunk:
            self.transport.write(chunk)
            reactor.callLater(0, self.sendChunk)
        else:
            print("File sent")
            self.file.close()
            self.transport.loseConnection()

class FileFactory(Factory):
    def buildProtocol(self, addr):
        return FileSender()
        
reactor.listenTCP(8080, FileFactory())
reactor.run()