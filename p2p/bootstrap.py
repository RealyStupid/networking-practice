from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

class BootstrapProtocol(Protocol):
    def connectionMade(self):
        peer_ip = self.transport.getPeer().host
        print(f"[BOOTSTRAP] Connection from {peer_ip}")

    def dataReceived(self, data):
        message = data.decode().strip()
        print(f"[BOOTSTRAP] Received: {message}")

        part = message.split()
        if len(part) == 2 and part[0] == "REGISTER":
            peer_port = part[1]
            peer_ip = self.transport.getPeer().host

            entry = f"{peer_ip}:{peer_port}"

            # Store this peer in the factory's list
            if entry not in self.factory.peers:
                self.factory.peers.append(entry)
                print(f"[BOOTSTRAP] Registered peer {entry}")

            # Send back the list of known peers
            peers_str = ",".join(self.factory.peers)
            response = f"PEERS {peers_str}\n"
            self.transport.write(response.encode())

        elif len(part) == 2 and part[0] == "UNREGISTER":
            peer_port = part[1]
            peer_ip = self.transport.getPeer().host

            entry = f"{peer_ip}:{peer_port}"

            if entry in self.factory.peers:
                self.factory.peers.remove(entry)
                print(f"[BOOTSTRAP] Unregistered peer {entry}")

            self.transport.write(b"OK\n")
            
        else:
            self.transport.write(b"ERROR invalid command\n")

class BootstrapFactory(Factory):
    def __init__(self):
        # List of strings like "ip:port"
        self.peers = []

    def buildProtocol(self, addr):
        proto = BootstrapProtocol()
        proto.factory = self
        return proto

if __name__ == "__main__":
    # Listen on port 9000 for peer registrations
    reactor.listenTCP(9000, BootstrapFactory())
    print("[BOOTSTRAP] Listening on port 9000")
    reactor.run()