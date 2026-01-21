import time
import threading
from typing import Tuple, Optional
from picoNet.socket import PicoSocket
from picoNet.packet import Packet, PacketHeader, PROTOCOL_ID, pack_packet, unpack_packet
from picoNet.serializer import serialize, deserialize

class NetworkClient:
    def __init__(self, server_ip: str, server_port: int, player_id: str):
        self.server_addr = (server_ip, server_port)
        self.player_id = player_id
        self.socket = PicoSocket("0.0.0.0", 0) # Random port
        self.running = True
        self.inbox = [] # Store received messages for the main thread
        
        # Start listener thread
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()
        
        self.send_login()

    def _listen(self):
        while self.running:
            result = self.socket.receive()
            if result:
                data, addr = result
                # Only accept from server
                if addr != self.server_addr:
                    continue
                    
                try:
                    packet = unpack_packet(data)
                    if packet.header.protocol_id == PROTOCOL_ID:
                        payload = deserialize(packet.payload)
                        self.inbox.append(payload)
                except Exception as e:
                    print(f"Network Error: {e}")
            else:
                time.sleep(0.001)

    def send(self, data: dict):
        payload_bytes = serialize(data)
        header = PacketHeader()
        packet = Packet(header, payload_bytes)
        packet_bytes = pack_packet(packet)
        self.socket.send(self.server_addr, packet_bytes)

    def send_login(self):
        self.send({
            "command": "login",
            "player_id": self.player_id
        })

    def send_attack(self, lines: int, target_id: Optional[str] = None):
        self.send({
            "command": "attack",
            "lines": lines,
            "target_id": target_id, # Optional, server can decide target
            "player_id": self.player_id
        })

    def get_messages(self):
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs

    def close(self):
        self.running = False
        self.socket.close()
