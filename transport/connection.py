# transport/connection.py
import asyncio
import socket
import time
from transport.sr import SelectiveRepeat
from shim.lossy import LossySocket
from metrics.metric_logger import MetricLogger

class Connection:
    def __init__(self, loop, addr, loss_rate=0.05, burst=False):
        """
        loop : asyncio event loop
        addr : (ip, port) tuple of the remote endpoint
        loss_rate : packet loss rate (0.0 - 1.0)
        burst : True to simulate bursty loss
        """
        self.loop = loop
        self.addr = addr
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setblocking(False)
        self.sock = LossySocket(self.udp_sock, loss_rate=loss_rate, burst=burst)

        # Metrics logger
        self.metrics = MetricLogger()

        # Selective Repeat ARQ
        self.sr = SelectiveRepeat(loop)
        self.sr.set_conn(self)
        self.sr.set_recv_callback(self._on_payload)

        # Callback for received messages
        self.on_msg_cb = None

        # Start receiving task
        asyncio.ensure_future(self._handle_receive())

    def on_message(self, cb):
        """Set callback for incoming messages"""
        self.on_msg_cb = cb

    def send_msg(self, msg_bytes):
        """Send a message reliably"""
        self.metrics.log_send()
        asyncio.ensure_future(self.sr.send(msg_bytes))

    async def _handle_receive(self):
        """Receive loop using lossy socket"""
        while True:
            try:
                data, _ = await self.sock.recvfrom(4096)
                sent_time = time.time()  # optional: track latency
                payload = await self.sr.receive(data)
                if payload:
                    seq = 0  # optional: extract sequence if needed
                    self.metrics.log_receive(seq, sent_time)
            except Exception as e:
                print("Receive error:", e)
                await asyncio.sleep(0.01)

    def _on_payload(self, payload):
        """Called when SelectiveRepeat delivers an in-order payload"""
        if self.on_msg_cb:
            self.on_msg_cb(payload)

    def get_metrics(self):
        return self.metrics.get_stats()

    def close(self):
        """Close socket cleanly"""
        self.udp_sock.close()


