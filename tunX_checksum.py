import os
import fcntl
import struct
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

def checksum(data):
    """
    Calculate the Internet Checksum of the data.
    """
    if len(data) % 2:
        data += b'\0'
    s = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff

def respond_to_ping(tun_fd):
    print("Listening for ICMP packets...")
    while True:
        # Read a packet from the TUN interface
        packet = os.read(tun_fd, 2048)

        # Check if it's an ICMP echo request (ping)
        ip_header = packet[:20]
        icmp_packet = packet[20:]

        # ICMP type 8 is Echo Request
        if icmp_packet[0] == 8:
            print("Received an ICMP Echo Request")

            # Create an ICMP Echo Reply
            icmp_type = 0  # Echo Reply
            icmp_code = 0
            icmp_checksum = 0
            icmp_id, icmp_seq = struct.unpack('!HH', icmp_packet[4:8])
            icmp_payload = icmp_packet[8:]
            icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
            icmp_checksum = checksum(icmp_header + icmp_payload)
            icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)

            # Swap source and destination IP addresses
            src_ip = ip_header[12:16]
            dest_ip = ip_header[16:20]
            swapped_ip_header = ip_header[:12] + dest_ip + src_ip + ip_header[20:]

            # Create final packet
            response = swapped_ip_header + icmp_header + icmp_payload

            # Write the response packet back to the TUN interface
            print("Sending ICMP Echo Reply")
            os.write(tun_fd, response)

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
