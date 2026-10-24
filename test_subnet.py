import contextlib
import io
import ipaddress
import os
import tempfile
import unittest

from calculator import calculate_subnet, iter_split, parse_network, split_network
from cli import main, parse_requirements
from vlsm import prefix_for_hosts, vlsm_calculate


class SubnetTests(unittest.TestCase):
    def test_basic_24(self):
        r = calculate_subnet("192.168.1.10/24")
        self.assertEqual(r["network"], "192.168.1.0")
        self.assertEqual(r["broadcast"], "192.168.1.255")
        self.assertEqual(r["first_host"], "192.168.1.1")
        self.assertEqual(r["last_host"], "192.168.1.254")
        self.assertEqual(r["usable_hosts"], 254)
        self.assertEqual(r["ip_type"], "Private")

    def test_input_formats_agree(self):
        a = calculate_subnet("10.0.0.5/30")
        self.assertEqual(a, calculate_subnet("10.0.0.5 255.255.255.252"))
        self.assertEqual(a, calculate_subnet("10.0.0.5/255.255.255.252"))

    def test_point_to_point_and_host_routes(self):
        self.assertEqual(calculate_subnet("10.0.0.0/31")["usable_hosts"], 2)
        self.assertEqual(calculate_subnet("1.1.1.1/32")["usable_hosts"], 1)

    def test_public_ip(self):
        self.assertEqual(calculate_subnet("8.8.8.8/24")["ip_type"], "Public")

    def test_special_ip_types(self):
        cases = {
            "10.1.2.3": "Private", "172.16.0.1": "Private", "192.168.1.1": "Private",
            "100.64.1.1": "Shared (CGNAT)", "127.0.0.1": "Loopback",
            "169.254.1.1": "Link-local", "224.0.0.5": "Multicast",
            "0.0.0.0": "Unspecified", "192.0.2.1": "Reserved", "240.0.0.1": "Reserved",
            "255.255.255.255": "Reserved", "1.1.1.1": "Public",
        }
        for ip, kind in cases.items():
            self.assertEqual(calculate_subnet(ip)["ip_type"], kind, ip)

    def test_invalid_input(self):
        for bad in ["", "300.1.1.1/24", "10.0.0.1/33", "abc", "10.0.0.1/255.0.255.0"]:
            with self.assertRaises(ValueError, msg=bad):
                parse_network(bad)

    def test_split(self):
        self.assertEqual(split_network("10.0.0.0/24", 26),
                         ["10.0.0.0/26", "10.0.0.64/26", "10.0.0.128/26", "10.0.0.192/26"])
        with self.assertRaises(ValueError):
            split_network("10.0.0.0/24", 24)

    def test_huge_split_is_lazy(self):
        count, subnets = iter_split("0.0.0.0/0", 32)
        self.assertEqual(count, 2 ** 32)
        self.assertEqual(next(subnets), "0.0.0.0/32")
        self.assertEqual(next(subnets), "0.0.0.1/32")
        with self.assertRaises(ValueError):    # validated up front, not on first next()
            iter_split("10.0.0.0/24", 20)


class VlsmTests(unittest.TestCase):
    def test_prefix_for_hosts(self):
        cases = {1: 30, 2: 30, 3: 29, 6: 29, 7: 28, 50: 26, 254: 24, 255: 23}
        for hosts, prefix in cases.items():
            self.assertEqual(prefix_for_hosts(hosts), prefix, hosts)

    def test_plan_is_largest_first_and_contiguous(self):
        reqs = [{"name": "Mgmt", "hosts": 10}, {"name": "Sales", "hosts": 50},
                {"name": "Eng", "hosts": 25}]
        r = vlsm_calculate("192.168.0.0/24", reqs)
        nets = [(s["name"], f"{s['network']}/{s['cidr']}") for s in r["subnets"]]
        self.assertEqual(nets, [("Sales", "192.168.0.0/26"),
                                ("Eng", "192.168.0.64/27"),
                                ("Mgmt", "192.168.0.96/28")])

    def test_no_overlap_and_inside_base(self):
        reqs = [{"name": str(i), "hosts": h} for i, h in enumerate([100, 60, 30, 12, 5, 2, 2])]
        r = vlsm_calculate("10.0.0.0/23", reqs)
        spans = sorted((int(ipaddress.ip_address(s["network"])),
                        int(ipaddress.ip_address(s["broadcast"]))) for s in r["subnets"])
        for (_, end), (start, _) in zip(spans, spans[1:]):
            self.assertLess(end, start)

    def test_too_big_fails(self):
        with self.assertRaises(ValueError):
            vlsm_calculate("192.168.0.0/26", [{"name": "A", "hosts": 50}, {"name": "B", "hosts": 30}])

    def test_requirement_parsing(self):
        self.assertEqual(parse_requirements(["Sales=50", "Eng:25"]),
                         [{"name": "Sales", "hosts": 50}, {"name": "Eng", "hosts": 25}])
        for bad in ["Sales", "Sales=x", "Sales=0", "=5"]:
            with self.assertRaises(ValueError, msg=bad):
                parse_requirements([bad])

    def test_requirement_names_with_separators(self):
        self.assertEqual(parse_requirements(["VLAN:10=50", "a=b:5"]),
                         [{"name": "VLAN:10", "hosts": 50}, {"name": "a=b", "hosts": 5}])

    def test_bad_csv_path_is_an_error_not_a_crash(self):
        path = os.path.join(tempfile.gettempdir(), "no-such-dir-xyz", "plan.csv")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = main(["vlsm", "10.0.0.0/24", "A=5", "--csv", path])
        self.assertEqual(code, 1)
        self.assertIn("could not save", err.getvalue())


if __name__ == "__main__":
    unittest.main()
