import socket
import fcntl
import struct
import multiprocessing

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x89115,
        struct.pack('256', bytes(ifname[:15], 'utf-8'))
    )[20: 24])

ip_addr = get_ip_address('eth0')

bind = f"{ip_addr}:8000"

workers = multiprocessing.cpu_count() * 2 + 1

preload = True