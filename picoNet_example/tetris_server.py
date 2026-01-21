import sys
import os
import time
import json
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picoNet.socket import PicoSocket
from picoNet.packet import Packet, PacketHeader, PROTOCOL_ID, pack_packet, unpack_packet
from picoNet.serializer import serialize, deserialize

# Extend Known Keys for Tetris
# Note: In a real scenario, we'd update serializer.py, but for now we'll rely on string keys mostly
# or just stick to 'command', 'player_id' which are known.

@dataclass
class PlayerSession:
    address: Tuple[str, int]
    player_id: str
    last_seen: float
    # Game State snapshot (simplified)
    score: int = 0
    board_preview: list = field(default_factory=list) # simplified grid

class TetrisServer:
    def __init__(self, port: int = 4242):
        self.socket = PicoSocket("0.0.0.0", port)
        self.players: Dict[str, PlayerSession] = {} # player_id -> Session
        self.address_map: Dict[Tuple[str, int], str] = {} # address -> player_id
        
        self.running = True
        print(f"Tetris Server started on port {port}")

    def run(self):
        while self.running:
            self._process_network()
            # Server tick updates could go here (e.g. matchmaking, timeout)
            time.sleep(0.001) # Avoid busy loop

    def _process_network(self):
        while True:
            result = self.socket.receive()
            if not result:
                break
            
            data, addr = result
            try:
                packet = unpack_packet(data)
                if packet.header.protocol_id != PROTOCOL_ID:
                    continue
                
                payload = deserialize(packet.payload)
                self._handle_message(payload, addr)
                
            except Exception as e:
                print(f"Error processing packet from {addr}: {e}")

    def _handle_message(self, message: dict, addr: Tuple[str, int]):
        cmd = message.get("command")
        
        if cmd == "login":
            self._handle_login(message, addr)
        elif cmd == "update":
            self._handle_update(message, addr)
        elif cmd == "attack":
            self._handle_attack(message, addr)

    def _handle_login(self, message: dict, addr: Tuple[str, int]):
        player_id = message.get("player_id")
        if not player_id:
            return
            
        print(f"Player {player_id} connected from {addr}")
        self.players[player_id] = PlayerSession(
            address=addr,
            player_id=player_id,
            last_seen=time.time()
        )
        self.address_map[addr] = player_id
        
        # Ack
        self._send_to(addr, {"command": "welcome", "server_time": time.time()})

    def _handle_update(self, message: dict, addr: Tuple[str, int]):
        # Received game state update from client
        player_id = self.address_map.get(addr)
        if not player_id:
            return

        session = self.players[player_id]
        session.last_seen = time.time()
        session.score = message.get("score", 0)
        
        # Broadcast to others?
        # For now, just print high scores occasionally or simple echo
        pass

    def _handle_attack(self, message: dict, addr: Tuple[str, int]):
        # Player sent garbage lines to opponent
        sender_id = self.address_map.get(addr)
        if not sender_id:
            return
            
        lines = message.get("lines", 0)
        target_id = message.get("target_id")
        
        if target_id and target_id in self.players:
            target_session = self.players[target_id]
            print(f"{sender_id} sent {lines} lines to {target_id}")
            
            self._send_to(target_session.address, {
                "command": "garbage",
                "lines": lines,
                "sender": sender_id
            })

    def _send_to(self, addr: Tuple[str, int], data: dict):
        payload_bytes = serialize(data)
        header = PacketHeader() # Defaults are fine for now
        packet = Packet(header, payload_bytes)
        packet_bytes = pack_packet(packet)
        self.socket.send(addr, packet_bytes)

if __name__ == "__main__":
    server = TetrisServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("Server stopping...")
        server.socket.close()
