from transport.packet import make_packet, parse_packet

def test_packet():
    data = b"Hello"
    pkt = make_packet(1, 1, 1, 0, 0, 8, data)
    parsed = parse_packet(pkt)
    assert parsed["payload"] == data
    print("Packet test passed")

if __name__ == "__main__":
    test_packet()
