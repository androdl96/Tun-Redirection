#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/if.h>
#include <linux/if_tun.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

// Constants for TUN interface.
#define IFF_TUN 0x0001
#define IFF_NO_PI 0x1000

int create_tun_interface(const char* name) {
    struct ifreq ifr;
    int fd = open("/dev/net/tun", O_RDWR);

    if (fd < 0) {
        perror("Opening /dev/net/tun");
        exit(1);
    }

    memset(&ifr, 0, sizeof(ifr));
    ifr.ifr_flags = IFF_TUN | IFF_NO_PI;
    strncpy(ifr.ifr_name, name, IFNAMSIZ);

    if (ioctl(fd, TUNSETIFF, (void*)&ifr) < 0) {
        perror("ioctl(TUNSETIFF)");
        close(fd);
        exit(1);
    }

    return fd;
}

void configure_interface(const char* name, const char* address) {
    char command[256];
    snprintf(command, sizeof(command), "ip addr add %s dev %s", address, name);
    system(command);
    snprintf(command, sizeof(command), "ip link set dev %s up", name);
    system(command);
}

unsigned short checksum(void* b, int len) {
    unsigned short* buf = b;
    unsigned int sum = 0;
    unsigned short result;

    for (sum = 0; len > 1; len -= 2)
        sum += *buf++;
    if (len == 1)
        sum += *(unsigned char*)buf;
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    result = ~sum;

    return result;
}

/*void send_packet(char* ip_packet, int packet_len, char* dest_ip) {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sock < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = inet_addr(dest_ip);

    if (sendto(sock, ip_packet, packet_len, 0, (struct sockaddr*)&dest, sizeof(dest)) < 0) {
        perror("Sendto failed");
    }

    close(sock);
}

void respond_to_ping(int tun_fd) {
    printf("Listening for ICMP packets...\n");
    char packet[2048];

    while (1) {
        int nread = read(tun_fd, packet, sizeof(packet));
        if (nread < 0) {
            perror("Reading from tun interface");
            break;
        }

        if (packet[20] == 8) {  // ICMP Echo Request
            printf("Received an ICMP Echo Request\n");

            // Create ICMP Echo Reply
            packet[20] = 0;  // Echo Reply
            unsigned short* icmp_header = (unsigned short*)(packet + 20);
            icmp_header[1] = 0; // Reset checksum to 0
            icmp_header[1] = checksum(icmp_header, nread - 20);

            // Swap source and destination IP
            for (int i = 0; i < 4; i++) {
                char temp = packet[12 + i];
                packet[12 + i] = packet[16 + i];
                packet[16 + i] = temp;
            }

            // Extract destination IP
            char dest_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, packet + 16, dest_ip, INET_ADDRSTRLEN);

            // Send the response packet
            printf("Sending response packet...\n");
            send_packet(packet, nread, dest_ip);  // Use nread as packet length
        }
    }
}*/

void send_packet(int sock, char* ip_packet, int packet_len, char* dest_ip) {
    struct sockaddr_in dest;
    memset(&dest, 0, sizeof(dest));
    dest.sin_family = AF_INET;
    dest.sin_addr.s_addr = inet_addr(dest_ip);

    if (sendto(sock, ip_packet, packet_len, 0, (struct sockaddr*)&dest, sizeof(dest)) < 0) {
        perror("Sendto failed");
    }
}

void respond_to_ping(int tun_fd) {
    printf("Listening for ICMP packets...\n");
    char packet[2048];

    // Open the socket once
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sock < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    while (1) {
        int nread = read(tun_fd, packet, sizeof(packet));
        if (nread < 0) {
            perror("Reading from tun interface");
            break;
        }

        if (packet[20] == 8) {  // ICMP Echo Request
            printf("Received an ICMP Echo Request\n");

            // Create ICMP Echo Reply
            packet[20] = 0;  // Echo Reply
            unsigned short* icmp_header = (unsigned short*)(packet + 20);
            icmp_header[1] = 0; // Reset checksum to 0
            icmp_header[1] = checksum(icmp_header, nread - 20);

            // Swap source and destination IP
            for (int i = 0; i < 4; i++) {
                char temp = packet[12 + i];
                packet[12 + i] = packet[16 + i];
                packet[16 + i] = temp;
            }

            // Extract destination IP
            char dest_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, packet + 16, dest_ip, INET_ADDRSTRLEN);

            // Send the response packet
            printf("Sending response packet...\n");
            send_packet(sock, packet, nread, dest_ip);  // Use nread as packet length
        }
    }

    // Close the socket when done
    close(sock);
}

int main() {
    int tun_fd = create_tun_interface("tunX");
    configure_interface("tunX", "10.0.0.10/24");

    printf("tunX interface created and configured. Listening for ICMP packets...\n");

    respond_to_ping(tun_fd);

    close(tun_fd);
    return 0;
}
