# transport/packet.py
import struct
import zlib

HEADER_FMT = "!B B H H H I"  # ver, flags, conn_id, seq, ack, checksum
HEADER_SIZE = struct.calcsize(HEADER_FMT)

class Packet:
    def __init__(self, seq=0, ack=0, payload=b'', conn_id=0, ver=1, flags=0):
        self.ver = ver
        self.flags = flags
        self.conn_id = conn_id
        self.seq = seq
        self.ack = ack
        self.payload = payload
        self.len = len(payload)
        self.checksum = self.calc_checksum()

    def calc_checksum(self):
        return zlib.crc32(self.payload) & 0xffffffff

    def pack(self):
        header = struct.pack(HEADER_FMT, self.ver, self.flags, self.conn_id, self.seq, self.ack, self.checksum)
        return header + self.payload

    @staticmethod
    def unpack(data):
        header = data[:HEADER_SIZE]
        payload = data[HEADER_SIZE:]
        ver, flags, conn_id, seq, ack, checksum = struct.unpack(HEADER_FMT, header)
        pkt = Packet(seq=seq, ack=ack, payload=payload, conn_id=conn_id, ver=ver, flags=flags)
        pkt.checksum = checksum
        if pkt.calc_checksum() != checksum:
            raise ValueError("Checksum mismatch")
        return pkt
