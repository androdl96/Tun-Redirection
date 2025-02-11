#!/usr/bin/env python3
import os
import fcntl
import struct
import socket
import time
from pyroute2 import IPRoute

# Constantes para configurar la interfaz TUN
TUNSETIFF = 0x400454ca
IFF_TUN   = 0x0001
IFF_NO_PI = 0x1000

def create_tun_interface(name='tunY'):
    # Abre el dispositivo TUN
    tun_fd = os.open('/dev/net/tun', os.O_RDWR)
    # Prepara la estructura para crear la interfaz TUN sin información adicional (IFF_NO_PI)
    ifr = struct.pack('16sH', name.encode('utf-8'), IFF_TUN | IFF_NO_PI)
    fcntl.ioctl(tun_fd, TUNSETIFF, ifr)
    return tun_fd

def configure_interface(name='tunY', address='10.0.0.100/24'):
    ip = IPRoute()
    idx_list = ip.link_lookup(ifname=name)
    if not idx_list:
        raise Exception(f'No se encontró la interfaz {name}')
    idx = idx_list[0]
    ip.addr('add', index=idx, address=address.split('/')[0], mask=int(address.split('/')[1]))
    ip.link('set', index=idx, state='up')
    ip.close()

def configure_route(dst_ip='192.168.222.1', interface='ens33'):
    ip = IPRoute()
    idx = ip.link_lookup(ifname=interface)[0]
    ip.route('add', dst=dst_ip, oif=idx)
    ip.close()

def calc_checksum(data):
    """
    Calcula el checksum (suma complementaria de 16 bits) para los datos.
    """
    s = 0
    # Si la longitud de los datos es impar, agrega un byte cero al final.
    if len(data) % 2 != 0:
        data += b'\x00'
    # Suma cada palabra de 16 bits
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i+1]
        s += word
        # Suma el acarreo
        s = (s & 0xffff) + (s >> 16)
    return ~s & 0xffff

def build_ip_header(src_ip, dst_ip, payload_len, identification=54321):
    """
    Construye el encabezado IP (20 bytes sin opciones)
    """
    version = 4
    ihl = 5
    ver_ihl = (version << 4) + ihl
    tos = 0
    total_length = 20 + payload_len  # Encabezado IP + payload
    flags_fragment_offset = 0
    ttl = 64
    protocol = socket.IPPROTO_ICMP
    checksum_ip = 0  # Inicialmente 0 para calcular el checksum
    src = socket.inet_aton(src_ip)
    dst = socket.inet_aton(dst_ip)
    ip_header = struct.pack('!BBHHHBBH4s4s',
                            ver_ihl,
                            tos,
                            total_length,
                            identification,
                            flags_fragment_offset,
                            ttl,
                            protocol,
                            checksum_ip,
                            src,
                            dst)
    checksum_ip = calc_checksum(ip_header)
    # Vuelve a empaquetar con el checksum correcto
    ip_header = struct.pack('!BBHHHBBH4s4s',
                            ver_ihl,
                            tos,
                            total_length,
                            identification,
                            flags_fragment_offset,
                            ttl,
                            protocol,
                            checksum_ip,
                            src,
                            dst)
    return ip_header

def build_icmp_echo_request(identifier=1, sequence=1, data=b'PingTest'):
    """
    Construye un paquete ICMP Echo Request.
    """
    icmp_type = 8  # Echo Request
    icmp_code = 0
    checksum_icmp = 0
    header = struct.pack('!BBHHH', icmp_type, icmp_code, checksum_icmp, identifier, sequence)
    # Calcular el checksum incluyendo el header y los datos
    checksum_icmp = calc_checksum(header + data)
    header = struct.pack('!BBHHH', icmp_type, icmp_code, checksum_icmp, identifier, sequence)
    return header + data

def main():
    tun_name = 'tunY'
    src_ip = '10.0.0.100'
    dst_ip = '192.168.222.130'
    interval = 2  # Intervalo de tiempo entre envíos (segundos)
    out_interface = 'ens33'

    print(f"Creando la interfaz TUN {tun_name} y asignándole la IP {src_ip}")
    tun_fd = create_tun_interface(tun_name)
    configure_interface(tun_name, address=f'{src_ip}/24')

    # Configurar la ruta específica para el destino
    #configure_route(dst_ip=dst_ip, interface=out_interface)

    # Espera breve para asegurarse de que la interfaz esté activa
    time.sleep(1)
    sequence_number = 1

    try:
        while True:
            # Construir el paquete ICMP Echo Request con datos de ejemplo
            icmp_packet = build_icmp_echo_request(identifier=1234, sequence=sequence_number, data=b'Hola mundo')
            payload_len = len(icmp_packet)
            ip_header = build_ip_header(src_ip, dst_ip, payload_len, identification=1000 + sequence_number)

            packet = ip_header + icmp_packet

            print(f"Enviando ICMP Echo Request {sequence_number} desde {src_ip} a {dst_ip} a través de {tun_name}")
            os.write(tun_fd, packet)
            print("Paquete enviado.")

            sequence_number += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Interrupción del usuario: deteniendo el envío de paquetes.")
    finally:
        os.close(tun_fd)

if __name__ == '__main__':
    main()
