import ipaddress
import math

def vlsm_calculate(network_input, requirements):
    try:
        network = ipaddress.ip_network(network_input, strict=True)
    except ValueError as e:
        return {"error": str(e)}

    requirements = sorted(requirements, key=lambda x: x["hosts"], reverse=True)

    results = []
    next_ip = int(network.network_address)
    network_end = int(network.broadcast_address)

    for req in requirements:
        needed_hosts = req["hosts"]
        bits = math.ceil(math.log2(needed_hosts + 2))
        prefix = 32 - bits

        subnet = ipaddress.ip_network(f"{ipaddress.ip_address(next_ip)}/{prefix}", strict=False)

        if int(subnet.broadcast_address) > network_end:
            return {"error": f"Not enough space in {network_input} for all requirements"}

        hosts = list(subnet.hosts())
        usable = max(subnet.num_addresses - 2, 0)

        results.append({
            "name": req["name"],
            "needed_hosts": needed_hosts,
            "network": str(subnet.network_address),
            "broadcast": str(subnet.broadcast_address),
            "subnet_mask": str(subnet.netmask),
            "cidr": prefix,
            "first_host": str(hosts[0]) if hosts else "N/A",
            "last_host": str(hosts[-1]) if hosts else "N/A",
            "usable_hosts": usable,
            "wasted": usable - needed_hosts,
            "size": subnet.num_addresses
        })

        next_ip = int(subnet.broadcast_address) + 1

    total_needed = sum(r["needed_hosts"] for r in results)
    total_allocated = sum(r["usable_hosts"] for r in results)
    total_size = network.num_addresses
    used_size = sum(r["size"] for r in results)

    return {
        "error": None,
        "network": network_input,
        "subnets": results,
        "total_needed": total_needed,
        "total_allocated": total_allocated,
        "total_wasted": total_allocated - total_needed,
        "total_size": total_size,
        "used_size": used_size,
        "free_size": total_size - used_size,
        "efficiency": round((total_needed / total_allocated) * 100, 1) if total_allocated else 0
    }