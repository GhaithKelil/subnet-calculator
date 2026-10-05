"""VLSM allocation: largest-first, smallest block that fits each requirement."""

import ipaddress

from calculator import host_range, parse_network


def prefix_for_hosts(hosts):
    """Smallest prefix length whose block holds `hosts` usable addresses."""
    if hosts < 1:
        raise ValueError("host count must be at least 1")
    bits = (hosts + 1).bit_length()                    # ceil(log2(hosts + 2)); network + broadcast
    if bits > 32:
        raise ValueError(f"{hosts} hosts do not fit in IPv4")
    return 32 - bits


def vlsm_calculate(network_input, requirements):
    """Allocate subnets inside `network_input`.

    requirements: list of {"name": str, "hosts": int}.
    Returns a result dict. Raises ValueError on bad input or if the plan does not fit.
    """
    _, network = parse_network(network_input)
    if not requirements:
        raise ValueError("at least one requirement is needed")

    ordered = sorted(requirements, key=lambda r: r["hosts"], reverse=True)

    results = []
    next_ip = int(network.network_address)
    end = int(network.broadcast_address)

    for req in ordered:
        needed = req["hosts"]
        prefix = prefix_for_hosts(needed)
        size = 1 << (32 - prefix)

        # Largest-first keeps blocks aligned, but round up defensively.
        next_ip = (next_ip + size - 1) // size * size
        if next_ip + size - 1 > end:
            raise ValueError(f"not enough space in {network} for '{req['name']}' ({needed} hosts)")

        subnet = ipaddress.IPv4Network((next_ip, prefix))
        first, last, usable = host_range(subnet)
        results.append({
            "name": req["name"],
            "needed_hosts": needed,
            "network": str(subnet.network_address),
            "broadcast": str(subnet.broadcast_address),
            "subnet_mask": str(subnet.netmask),
            "cidr": prefix,
            "first_host": str(first),
            "last_host": str(last),
            "usable_hosts": usable,
            "wasted": usable - needed,
            "size": subnet.num_addresses,
        })
        next_ip += size

    total_needed = sum(r["needed_hosts"] for r in results)
    total_usable = sum(r["usable_hosts"] for r in results)
    used = sum(r["size"] for r in results)
    return {
        "network": str(network),
        "subnets": results,
        "total_needed": total_needed,
        "total_allocated": total_usable,
        "total_wasted": total_usable - total_needed,
        "total_size": network.num_addresses,
        "used_size": used,
        "free_size": network.num_addresses - used,
        "efficiency": round(total_needed / total_usable * 100, 1) if total_usable else 0.0,
    }
