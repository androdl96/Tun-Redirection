sudo ip tuntap add dev tunA mode tun
sudo ip addr add 10.0.0.15/24 dev tunA
sudo ip link set dev tunA up