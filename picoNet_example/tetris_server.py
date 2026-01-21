import sys
import os
import time
import random
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from picoNet.socket import PicoSocket
from picoNet.packet import Packet, PacketHeader, PROTOCOL_ID, pack_packet, unpack_packet
from picoNet.serializer import serialize, deserialize

@dataclass
class PlayerSession:
    address: Tuple[str, int]
    player_id: str
    last_seen: float
    score: int = 0
    grid: list = field(default_factory=list)

class TetrisServer:
    def __init__(self, port: int = 4242):
        self.socket = PicoSocket("0.0.0.0", port)
        self.players: Dict[str, PlayerSession] = {} # player_id -> Session
        self.address_map: Dict[Tuple[str, int], str] = {} # address -> player_id
        self.match_seed = random.randint(0, 999999)
        
        self.running = True
        print(f"Tetris Server started on port {port}. Match Seed: {self.match_seed}")

    def run(self):
        while self.running:
            self._process_network()
            # Cleanup stale players (e.g. 30s timeout)
            now = time.time()
            stale = [pid for pid, s in self.players.items() if now - s.last_seen > 30]
            for pid in stale:
                print(f"Player {pid} timed out.")
                addr = self.players[pid].address
                if addr in self.address_map: del self.address_map[addr]
                del self.players[pid]
                
            time.sleep(0.001)

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
                pass # Silently ignore malformed

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
        if not player_id: return
            
        print(f"Player {player_id} connected from {addr}")
        
        # If player already exists, update address
        if player_id in self.players:
            old_addr = self.players[player_id].address
            if old_addr in self.address_map: del self.address_map[old_addr]
            
        self.players[player_id] = PlayerSession(
            address=addr,
            player_id=player_id,
            last_seen=time.time()
        )
        self.address_map[addr] = player_id
        
        self._send_to(addr, {
            "command": "welcome", 
            "server_time": time.time(),
            "match_seed": self.match_seed
        })

    def _handle_update(self, message: dict, addr: Tuple[str, int]):
        player_id = self.address_map.get(addr)
        if not player_id: return

        session = self.players[player_id]
        session.last_seen = time.time()
        session.score = message.get("score", 0)
        session.grid = message.get("grid", [])
        
        # Broadcast this update to everyone ELSE
        update_pkg = {
            "command": "opponent_update",
            "player_id": player_id,
            "score": session.score,
            "grid": session.grid
        }
        
        for pid, other in self.players.items():
            if pid != player_id:
                self._send_to(other.address, update_pkg)

    def _handle_attack(self, message: dict, addr: Tuple[str, int]):
        sender_id = self.address_map.get(addr)
        if not sender_id: return
            
        lines = message.get("lines", 0)
        target_id = message.get("target_id")
        
        if not target_id:
            potential_targets = [pid for pid in self.players if pid != sender_id]
            if potential_targets:
                target_id = random.choice(potential_targets)
        
        if target_id and target_id in self.players and target_id != sender_id:
            target_session = self.players[target_id]
            print(f"ATTACK: {sender_id} -> {target_id} ({lines} lines)")
            
            self._send_to(target_session.address, {
                "command": "garbage",
                "lines": lines,
                "sender": sender_id
            })

    def _send_to(self, addr: Tuple[str, int], data: dict):
        try:
            payload_bytes = serialize(data)
            header = PacketHeader()
            packet = Packet(header, payload_bytes)
            self.socket.send(addr, pack_packet(packet))
        except:
            pass

if __name__ == "__main__":
    server = TetrisServer()
    try:
        server.run()
    except KeyboardInterrupt:
        server.socket.close()