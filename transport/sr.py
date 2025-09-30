# transport/sr.py
import asyncio
import time
from transport.packet import Packet

class SelectiveRepeat:
    def __init__(self, loop, window_size=5, timeout=0.5):
        self.loop = loop
        self.window_size = window_size
        self.timeout = timeout
        self.send_base = 0
        self.next_seq = 0
        self.send_buffer = {}  # seq -> (Packet, timestamp)
        self.recv_buffer = {}  # seq -> Packet
        self.recv_callback = None
        self.conn = None

    def set_conn(self, conn):
        self.conn = conn

    async def send(self, payload):
        if self.next_seq < self.send_base + self.window_size:
            pkt = Packet(seq=self.next_seq, payload=payload)
            self.send_buffer[self.next_seq] = (pkt, time.time())
            self.conn.sock.sendto(pkt.pack(), self.conn.addr)
            self.loop.create_task(self._retransmit(pkt.seq))
            self.next_seq += 1
        else:
            # Window full; wait until ACK frees up
            await asyncio.sleep(0.05)
            await self.send(payload)

    async def _retransmit(self, seq):
        while seq in self.send_buffer:
            pkt, ts = self.send_buffer[seq]
            if time.time() - ts > self.timeout:
                self.conn.sock.sendto(pkt.pack(), self.conn.addr)
                self.send_buffer[seq] = (pkt, time.time())
            await asyncio.sleep(self.timeout / 2)

    async def receive(self, data):
        try:
            pkt = Packet.unpack(data)
        except ValueError:
            return None

        # Handle ACK
        if pkt.ack in self.send_buffer:
            del self.send_buffer[pkt.ack]
            self.send_base = min(self.send_buffer.keys(), default=self.next_seq)

        # Handle payload
        if pkt.seq >= self.send_base:
            self.recv_buffer[pkt.seq] = pkt
            # Send ACK
            ack_pkt = Packet(seq=0, ack=pkt.seq, payload=b'')
            self.conn.sock.sendto(ack_pkt.pack(), self.conn.addr)
            # Deliver in-order messages
            self._deliver_in_order()
        return pkt.payload

    def _deliver_in_order(self):
        while self.send_base in self.recv_buffer:
            pkt = self.recv_buffer.pop(self.send_base)
            if self.recv_callback:
                self.recv_callback(pkt.payload)
            self.send_base += 1

    def set_recv_callback(self, cb):
        self.recv_callback = cb
