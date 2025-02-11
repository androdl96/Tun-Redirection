import os
import fcntl
import struct
import subprocess
from ctypes import *

# Constants from <linux/if_tun.h>
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001

# Constants from <linux/if.h>
IFNAMSIZ = 16

class Ifreq(Structure):
    _fields_ = [("ifr_name", c_char * IFNAMSIZ),
                ("ifr_flags", c_short)]

def create_tun_interface(tun_name):
    # Open TUN device
    tun_fd = os.open("/dev/net/tun", os.O_RDWR)

    # Prepare the ifreq structure
    ifr = Ifreq()
    ifr.ifr_flags = IFF_TUN
    ifr.ifr_name = tun_name.encode('utf-8')

    # Create TUN interface
    fcntl.ioctl(tun_fd, TUNSETIFF, ifr)

    return tun_fd

def configure_interface(tun_name, ip_address):
    # Assign IP address to the TUN interface
    subprocess.run(["ip", "addr", "add", f"{ip_address}/24", "dev", tun_name], check=True)

    # Bring the interface up
    subprocess.run(["ip", "link", "set", "dev", tun_name, "up"], check=True)

def main():
    tun_name = "tunZ"
    ip_address = "10.0.0.50"

    tun_fd = create_tun_interface(tun_name)
    print(f"TUN interface {tun_name} created.")

    configure_interface(tun_name, ip_address)
    print(f"Assigned IP {ip_address} to {tun_name} and brought it up.")

    try:
        # Keep the program running to keep the interface open
        while True:
            os.read(tun_fd, 4096)
    except KeyboardInterrupt:
        print("Closing TUN interface.")
    finally:
        os.close(tun_fd)

if __name__ == "__main__":
    main()
