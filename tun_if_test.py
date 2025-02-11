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

def respond_to_ping(tun_fd):
    print("A: Listening for ICMP packets...")
    while True:
        # Read a packet from the TUN interface
        packet = os.read(tun_fd, 2048)
        #print("B: Received a packet of length %d" % len(packet))
        # Check if it's an ICMP echo request (ping)
        if packet[20] == 8:  # ICMP type 8 is Echo Request
            #pass
            
            print("Received an ICMP Echo Request")
            # Create an ICMP Echo Reply
            response = packet[:20] + b'\x00' + packet[21:]

            # Swap source and destination IP addresses
            response = response[:12] + response[16:20] + response[12:16] + response[20:]

            # Write the response packet back to the TUN interface
            print("C: Modified the packet and sending it back")
            os.write(tun_fd, response)

            #print("D: Not sending anything back")
            
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
