sudo tc qdisc del dev tunX handle ffff: ingress

sudo tc qdisc add dev tunX handle ffff: ingress
sudo tc filter add dev tunX parent ffff: protocol ip prio 1 flower ip_proto icmp dst_ip 192.168.222.128 action mirred egress redirect dev tunY


