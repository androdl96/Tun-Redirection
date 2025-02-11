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

def checksum(source_string):
    """
    Calculate the checksum of the input string
    """
    sum = 0
    max_count = (len(source_string) // 2) * 2
    count = 0
    while count < max_count:
        val = source_string[count + 1] * 256 + source_string[count]
        sum = sum + val
        sum = sum & 0xffffffff
        count = count + 2

    if max_count < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def send_packet(ip_packet, dest_ip):
    # Create a raw socket with AF_INET
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    try:
        # Send the packet
        sock.sendto(ip_packet, (dest_ip, 0))
    finally:
        sock.close()

def read_from_tun(tun_fd):
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

        # Check if the destination IP is 192.168.222.128
        if dest_ip == '192.168.222.128':
            print(f"Forwarding packet to {dest_ip} via AF_INET socket")
            send_packet(packet, dest_ip)

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
