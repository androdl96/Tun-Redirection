sudo tc qdisc del dev ens33 handle ffff: ingress
#sudo tc qdisc del dev tunX handle ffff: ingress

sudo tc qdisc add dev ens33 handle ffff: ingress
sudo tc filter add dev ens33 parent ffff: protocol ip prio 1 flower ip_proto icmp src_ip 192.168.222.1 action mirred egress redirect dev tunX
#sudo tc filter add dev ens33 parent ffff: protocol ip prio 1 action mirred egress redirect dev tunX

#sudo tc qdisc add dev tunX handle ffff: ingress
#sudo tc filter add dev tunX parent ffff: protocol ip prio 1 flower ip_proto icmp dst_ip 192.168.222.1 action mirred egress redirect dev ens33

