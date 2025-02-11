import os
import fcntl
import struct
import socket
from pyroute2 import IPRoute

# Constants for TUN interface
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

def create_tun_interface(name='tunX'):
    # Open the TUN device file using os.open
    tun_fd = os.open('/dev/net/tun', os.O_RDWR)
    
    # Create the TUN interface
    ifr = struct.pack('16sH', name.encode('utf-8'), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun_fd, TUNSETIFF, ifr)
    
    return tun_fd

def configure_interface(name='tunX', address='10.0.0.10/24'):
    ip = IPRoute()
    idx = ip.link_lookup(ifname=name)[0]
    ip.addr('add', index=idx, address=address.split('/')[0], mask=int(address.split('/')[1]))
    ip.link('set', index=idx, state='up')

def send_packet(ip_packet, dest_ip):
    # Create a raw socket with AF_INET
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    try:
        # Send the packet
        sock.sendto(ip_packet, (dest_ip, 0))
    finally:
        sock.close()

def respond_to_ping(tun_fd):
    print("Listening for ICMP packets...")
    while True:
        # Read a packet from the TUN interface
        packet = os.read(tun_fd, 2048)
        # Check if it's an ICMP echo request (ping)
        if packet[20] == 8:  # ICMP type 8 is Echo Request
            print("Received an ICMP Echo Request")
            # Create an ICMP Echo Reply
            response = packet[:20] + b'\x00' + packet[21:]

            # Swap source and destination IP addresses
            response = response[:12] + response[16:20] + response[12:16] + response[20:]

            # Extract destination IP
            dest_ip = socket.inet_ntoa(packet[12:16])

            # Send the response packet via appropriate interface
            print("Sending response packet via ens33")
            send_packet(response, dest_ip)

def main():
    tun_fd = create_tun_interface()
    configure_interface()
    try:
        print("tunX interface created and configured. Listening for ICMP packets...")
        respond_to_ping(tun_fd)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        os.close(tun_fd)

if __name__ == '__main__':
    main()
