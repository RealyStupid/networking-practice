from twisted.internet.protocol import Protocol, ClientFactory, Factory
from twisted.internet import reactor, stdio
from twisted.protocols import basic

BOOTSTRAP_HOST = "127.0.0.1"
BOOTSTRAP_PORT = 9000

username = input("Enter username: ").strip()

# Simple shared key for XOR "encryption"
SHARED_KEY = b"OOOpyGOOpySooopererSecret"

def xor_bytes(data: bytes, key: bytes) -> bytes:
    """
    XOR each byte of data with the key (repeated).
    """
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))

def encrypt_message(plaintext: str) -> bytes:
    """
    Take a string, encode to bytes, XOR with key.
    Returns encrypted bytes.
    """
    raw = plaintext.encode()
    return xor_bytes(raw, SHARED_KEY)

def decrypt_message(ciphertext: bytes) -> str:
    """
    Take encrypted bytes, XOR with key, decode to string.
    """
    raw = xor_bytes(ciphertext, SHARED_KEY)
    return raw.decode()

# PEER PROTOCOL (handles one peer connection)
class PeerProtocol(Protocol):
    """
    This protocol handles a single connection to another peer.
    It is used for BOTH incoming and outgoing peer connections.
    """

    def connectionMade(self):
        peer = self.transport.getPeer()
        print(f"[PEER] Connected to peer {peer.host}:{peer.port}")

        # Add this connection to the shared list
        self.factory.peer_connections.append(self)

    def dataReceived(self, data):
        """
        Called when a peer sends us data.
        Data is encrypted bytes; we decrypt then print.
        """
        try:
            message = decrypt_message(data).strip()
        except Exception as e:
            print(f"[PEER] Failed to decrypt message: {e}")
            return

        print(message)

    def connectionLost(self, reason):
        """
        Called when a peer disconnects.
        """
        if self in self.factory.peer_connections:
            self.factory.peer_connections.remove(self)
        print("[PEER] Peer disconnected")

# SERVER FACTORY (incoming connections)
class PeerFactory(Factory):
    """
    This factory creates PeerProtocol instances for incoming connections.
    It also stores the shared list of active peer connections.
    """

    def __init__(self):
        self.peer_connections = []

    def buildProtocol(self, addr):
        proto = PeerProtocol()
        proto.factory = self
        return proto

# CLIENT FACTORY (outgoing connections)
class PeerClientFactory(ClientFactory):
    """
    This factory is used when we CONNECT to another peer.
    It shares the same peer_connections list as the server factory.
    """

    def __init__(self, peer_factory):
        self.peer_factory = peer_factory

    def buildProtocol(self, addr):
        proto = PeerProtocol()
        proto.factory = self.peer_factory
        return proto

    def startedConnecting(self, connector):
        print("[PEER] Starting connection to peer...")

    def clientConnectionFailed(self, connector, reason):
        print("[PEER] Connection to peer failed:", reason)

    def clientConnectionLost(self, connector, reason):
        print("[PEER] Lost connection to peer:", reason)

# BOOTSTRAP CLIENT PROTOCOL
class BootstrapClientProtocol(Protocol):
    """
    Handles the connection to the bootstrap server.
    We only use this once at startup.
    """

    def connectionMade(self):
        print("[BOOTSTRAP-CLIENT] Connected to bootstrap server")
        register_cmd = f"REGISTER {LISTEN_PORT}\n"
        self.transport.write(register_cmd.encode())

    def dataReceived(self, data):
        message = data.decode().strip()
        print(f"[BOOTSTRAP-CLIENT] Received: {message}")

        if message.startswith("PEERS "):
            peers_str = message[len("PEERS "):]

            if peers_str:
                peers = peers_str.split(",")

                for entry in peers:
                    ip, port_str = entry.split(":")
                    port = int(port_str)

                    # Don't connect to ourselves
                    if port == LISTEN_PORT:
                        continue

                    print(f"[BOOTSTRAP-CLIENT] Connecting to peer {ip}:{port}")
                    reactor.connectTCP(ip, port, PeerClientFactory(peer_factory))

        # Done with bootstrap
        self.transport.loseConnection()

class BootstrapClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        proto = BootstrapClientProtocol()
        proto.factory = self
        return proto

    def clientConnectionFailed(self, connector, reason):
        print("[BOOTSTRAP-CLIENT] Failed to connect to bootstrap:", reason)

# STDIN HANDLER
class StdinInput(basic.LineReceiver):
    """
    Reads lines from stdin and broadcasts them to all connected peers.
    """

    delimiter = b"\n"

    def __init__(self, peer_factory):
        self.peer_factory = peer_factory

    def lineReceived(self, line):
        text = line.decode().strip()
        if not text:
            return

        if text == "/quit":
            print("[PEER] Quitting and unregistering from bootstrap...")
            send_unregister_and_quit()
            return
        
        # Build the cleartext name
        message = f"[{username}] {text}\n"

        # Encrypt the message
        data = encrypt_message(message)

        # Broadcast to all peers
        for proto in self.peer_factory.peer_connections:
            proto.transport.write(data)

# unregister the client
class UnregisterProtocol(Protocol):
    def __init__(self, cmd):
        self.cmd = cmd

    def connectionMade(self):
        self.transport.write(self.cmd.encode())

    def dataReceived(self, data):
        print("[BOOTSTRAP] Unregister response:", data.decode().strip())
        self.transport.loseConnection()

class UnregisterClientFactory(ClientFactory):
    def __init__(self, cmd):
        self.cmd = cmd

    def buildProtocol(self, addr):
        return UnregisterProtocol(self.cmd)
    
def send_unregister_and_quit():
    cmd = f"UNREGISTER {LISTEN_PORT}\n"
    reactor.connectTCP(
        BOOTSTRAP_HOST,
        BOOTSTRAP_PORT,
        UnregisterClientFactory(cmd)
    )
    # Give it a moment, then stop reactor
    reactor.callLater(0.2, reactor.stop)

# MAIN PROGRAM
if __name__ == "__main__":
    # 1. Start listening for incoming peer connections
    peer_factory = PeerFactory()
    port_obj = reactor.listenTCP(0, peer_factory)
    LISTEN_PORT = port_obj.getHost().port
    print(f"[PEER] Listening for peers on port {LISTEN_PORT}")

    # 2. Connect to bootstrap server
    reactor.connectTCP(BOOTSTRAP_HOST, BOOTSTRAP_PORT, BootstrapClientFactory())
    print(f"[PEER] Connecting to bootstrap at {BOOTSTRAP_HOST}:{BOOTSTRAP_PORT}")

    # 3. Attach stdin handler
    stdio.StandardIO(StdinInput(peer_factory))

    # 4. Start reactor
    reactor.run()