# Tun-Redirection

Some examples regarding [this problem](https://stackoverflow.com/questions/79421852/tc-filter-redirection-one-way-behavior-issue-with-icmp-ping-replies)

* `tun_if_test.py`: creates and configures a TUN interface on a Linux system, assigns it an IP address, and listens for ICMP echo requests (pings) on the interface. When a ping request is received, it responds with an ICMP echo reply, effectively simulating a ping response.

* `gen_request.py` : This script creates and configures a TUN interface named 'tunY' on a Linux system with a specified IP address, then repeatedly constructs and sends ICMP Echo Request (ping) packets from a source IP to a destination IP at regular intervals, simulating network traffic through the TUN interface.

* `add_if_tunZ.py` : This script creates a TUN interface named 'tunZ' on a Linux system, assigns it the IP address '10.0.0.50', and brings the interface up using system calls and subprocess commands. It then keeps the interface open, reading data continuously until interrupted by the user.

