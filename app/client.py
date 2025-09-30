import asyncio, socket, sys
from transport.connection import Connection

async def run_client(server_host="127.0.0.1", server_port=9000):
    loop = asyncio.get_event_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    conn = Connection(loop, sock, (server_host, server_port))

    conn.on_message(lambda msg: print("SERVER:", msg.decode()))

    async def input_loop():
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            conn.send_msg(line.strip().encode())

    async def recv_loop():
        while True:
            data, addr = await loop.sock_recvfrom(sock, 4096)
            conn.conn.handle_packet(data)

    await asyncio.gather(input_loop(), recv_loop())

if __name__ == "__main__":
    asyncio.run(run_client())
