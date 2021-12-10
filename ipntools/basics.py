import socket
import random
import struct

def generateIp() -> None:
    ip = socket.inet_ntoa(struct.pack(">I", random.randint(1, 0xffffffff)))
    return ip