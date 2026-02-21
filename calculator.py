import ipaddress

def calculate_subnet(ip_input):
    try:
        network = ipaddress.ip_network(ip_input, strict=False)
        ip = ipaddress.ip_address(ip_input.split("/")[0])

        usable_hosts = list(network.hosts())
        first_host = usable_hosts[0] if usable_hosts else "N/A"
        last_host = usable_hosts[-1] if usable_hosts else "N/A"

        is_private = ip.is_private

        print("\n========== SUBNET CALCULATOR ==========")
        print(f"  IP Address       : {ip}")
        print(f"  Network Address  : {network.network_address}")
        print(f"  Broadcast        : {network.broadcast_address}")
        print(f"  Subnet Mask      : {network.netmask}")
        print(f"  Wildcard Mask    : {network.hostmask}")
        print(f"  CIDR Notation    : {network.prefixlen}")
        print(f"  First Host       : {first_host}")
        print(f"  Last Host        : {last_host}")
        print(f"  Usable Hosts     : {network.num_addresses - 2}")
        print(f"  IP Type          : {'Private' if is_private else 'Public'}")
        print("========================================\n")

    except ValueError as e:
        print(f"Invalid input: {e}")

def main():
    print("Subnet Calculator")
    print("Enter IP with CIDR (e.g. 192.168.1.1/24) or IP and mask (e.g. 192.168.1.1 255.255.255.0)")
    
    while True:
        user_input = input("\nEnter IP (or 'q' to quit): ").strip()
        
        if user_input.lower() == "q":
            break
        
        if " " in user_input:
            parts = user_input.split()
            ip = parts[0]
            mask = parts[1]
            user_input = f"{ip}/{ipaddress.IPv4Network(f'0.0.0.0/{mask}').prefixlen}"
        
        calculate_subnet(user_input)

if __name__ == "__main__":
    main()