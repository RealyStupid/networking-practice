from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet import reactor
from twisted.internet import stdio
from twisted.protocols import basic

# To encrypt the message!
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class ChatCLient(Protocol):
    def connectionMade(self):
        print("-- Connected to Server --")
        self.transport.write(username + b"\n")

    def dataReceived(self, data):
        print(data.decode(), end="")

    def connectionLost(self, reason):
        print("-- Connection lost/terminated --")
        if reactor.running:
            reactor.stop()

class StdinInput(basic.LineReceiver):
    delimiter = b"\n"

    def __init__(self, protocol):
        self.protocol = protocol

    def lineReceived(self, line):
        self.protocol.transport.write(line + b"\n")
    
class ChatClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        proto = ChatCLient()
        stdio.StandardIO(StdinInput(proto))
        return proto
    
if __name__ == "__main__":
    username = input("Please give a username: ").strip().encode()
    reactor.connectTCP("127.0.0.1", 8080, ChatClientFactory())
    reactor.run()