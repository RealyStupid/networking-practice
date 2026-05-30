from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

class ChatProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.username = None

    # this fires when a client joines. For this one we first append to the users list and then tell everyone the user joined
    def connectionMade(self):
        self.factory.clients.append(self)
        #self.transport.write(b"What should we call you? \n")

    # this fires when a client leaves. For this one we first append to the users list and then tell everyone the user left
    def connectionLost(self, reason):
        if self in self.factory.clients:
            self.factory.clients.remove(self)
        if self.username:
            self.broadcast(f"[SYSTEM] {self.username} left the chat.\n")
            print(f"[SYSTEM] {self.username} left the chat.")

    # allows us to recieve data sent by the user
    def dataReceived(self, data):
        message = data.decode().strip()

        # first message is username
        if self.username is None:
            self.username = message
            self.broadcast(f"[SYSTEM] {self.username} joined the chat.\n")
            print(f"[SYSTEM] {self.username} joined the chat.")

            return
        
        # regular messages
        self.broadcast(f"[{self.username}] {message}\n")

    # we loop through evey client in the chat and send the same message to them
    def broadcast(self, message):
        for client in self.factory.clients:
            if client is not self:
                client.transport.write(message.encode())

class ChatFactory(Factory):
    def __init__(self):
        self.clients = [] # Shared memory for all clients

    def buildProtocol(self, addr):
        return ChatProtocol(self)
    
#we start the server
if __name__ == "__main__":
    reactor.listenTCP(8080, ChatFactory())
    reactor.run()