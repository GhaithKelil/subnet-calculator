"""Core IPv4 subnet maths. Pure functions, no I/O."""

import ipaddress


def parse_network(text):
    """Parse '192.168.1.10/24', '192.168.1.10 255.255.255.0' or
    '192.168.1.10/255.255.255.0' into (IPv4Address, IPv4Network).

    Raises ValueError with a readable message on bad input.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("input is empty")

    if "/" in text:
        addr, _, mask = text.partition("/")
    elif " " in text:
        addr, _, mask = text.partition(" ")
    else:
        addr, mask = text, "32"
    addr, mask = addr.strip(), mask.strip()

    try:
        ip = ipaddress.IPv4Address(addr)
    except ValueError:
        raise ValueError(f"'{addr}' is not a valid IPv4 address") from None

    try:
        network = ipaddress.IPv4Network(f"{ip}/{mask}", strict=False)
    except ValueError:
        raise ValueError(f"'{mask}' is not a valid prefix length or subnet mask") from None

    return ip, network


def host_range(network):
    """Return (first_host, last_host, usable_count) following RFC 3021 for /31 and /32."""
    size = network.num_addresses
    base = int(network.network_address)
    if size == 1:                       # /32: single host
        return network.network_address, network.network_address, 1
    if size == 2:                       # /31: point-to-point, both usable
        return network.network_address, network.broadcast_address, 2
    return (ipaddress.IPv4Address(base + 1),
            ipaddress.IPv4Address(base + size - 2),
            size - 2)


def calculate_subnet(text):
    """Return a dict describing the subnet for the given input."""
    ip, network = parse_network(text)
    first, last, usable = host_range(network)
    return {
        "ip": str(ip),
        "network": str(network.network_address),
        "broadcast": str(network.broadcast_address),
        "subnet_mask": str(network.netmask),
        "wildcard": str(network.hostmask),
        "cidr": network.prefixlen,
        "first_host": str(first),
        "last_host": str(last),
        "usable_hosts": usable,
        "total_addresses": network.num_addresses,
        "ip_type": "Private" if ip.is_private else "Public",
        "binary_mask": ".".join(f"{o:08b}" for o in network.netmask.packed),
    }


def split_network(text, new_prefix):
    """Split a network into equal subnets of /new_prefix. Returns a list of CIDR strings."""
    _, network = parse_network(text)
    if not network.prefixlen < new_prefix <= 32:
        raise ValueError(f"new prefix must be larger than /{network.prefixlen} and at most /32")
    return [str(s) for s in network.subnets(new_prefix=new_prefix)]
