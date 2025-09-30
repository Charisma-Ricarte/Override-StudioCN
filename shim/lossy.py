import random, socket

LOSS_PROB = 0.1

def forward(src_port, dst_host, dst_port):
    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_in.bind(("127.0.0.1", src_port))
    sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        data, addr = sock_in.recvfrom(4096)
        if random.random() > LOSS_PROB:
            sock_out.sendto(data, (dst_host, dst_port))
