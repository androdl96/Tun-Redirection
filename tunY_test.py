import os
import fcntl
import struct
import socket
from pyroute2 import IPRoute

# Constants for TUN interface
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

def create_tun_interface(name='tunY'):
    # Open the TUN device file using os.open
    tun_fd = os.open('/dev/net/tun', os.O_RDWR)
    
    # Create the TUN interface
    ifr = struct.pack('16sH', name.encode('utf-8'), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun_fd, TUNSETIFF, ifr)
    
    return tun_fd

def configure_interface(name='tunY', address='10.0.1.10/24'):
    ip = IPRoute()
    idx = ip.link_lookup(ifname=name)[0]
    ip.addr('add', index=idx, address=address.split('/')[0], mask=int(address.split('/')[1]))
    ip.link('set', index=idx, state='up')

"""def read_from_tun(tun_fd):
    print("Listening on tunY for ICMP packets...")
    while True:
        # Read a packet from the TUN interface
        packet = os.read(tun_fd, 2048)

        # Extract the IP header (first 20 bytes)
        ip_header = packet[:20]
        iph = struct.unpack('!BBHHHBBH4s4s', ip_header)

        # Extract source and destination IP addresses
        src_ip = socket.inet_ntoa(iph[8])
        dest_ip = socket.inet_ntoa(iph[9])

        print(f"Received a packet: Source IP: {src_ip}, Destination IP: {dest_ip}")
"""

def read_from_tun(tun_fd):
    print("Listening on tunY for ICMP packets...")
    
    # Create a raw socket to send packets out through ens33
    try:
        raw_socket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        raw_socket.bind(('ens33', 0))
    except PermissionError:
        print("You need to run this script with sudo privileges to open a raw socket.")
        return

    while True:
        # Read a packet from the TUN interface
        packet = os.read(tun_fd, 2048)

        # Extract the IP header (first 20 bytes)
        ip_header = packet[:20]
        iph = struct.unpack('!BBHHHBBH4s4s', ip_header)

        # Extract source and destination IP addresses
        src_ip = socket.inet_ntoa(iph[8])
        dest_ip = socket.inet_ntoa(iph[9])

        print(f"Received a packet: Source IP: {src_ip}, Destination IP: {dest_ip}")

        # Check if the destination IP is 192.168.222.1
        if dest_ip == '192.168.222.128':
            print(f"Forwarding packet to ens33: {src_ip} -> {dest_ip}")
            # Send the packet out through the raw socket
            raw_socket.send(packet)

def main():
    tun_fd = create_tun_interface()
    configure_interface()
    try:
        print("tunY interface created and configured with IP 10.0.1.10. Listening for ICMP packets...")
        read_from_tun(tun_fd)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        os.close(tun_fd)

if __name__ == '__main__':
    main()
