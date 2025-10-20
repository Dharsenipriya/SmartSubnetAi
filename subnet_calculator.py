import ipaddress
from typing import List, Dict

class SubnetCalculator:
    """
    A tool to calculate optimal subnet allocations for data centers
    """
    
    def __init__(self, network: str):
        """
        Initialize with a network in CIDR notation (e.g., '192.168.1.0/24')
        """
        self.network = ipaddress.IPv4Network(network, strict=False)
        print(f"Network initialized: {self.network}")
        print(f"Network Address: {self.network.network_address}")
        print(f"Broadcast Address: {self.network.broadcast_address}")
        print(f"Total Hosts Available: {self.network.num_addresses - 2}")
        print(f"Netmask: {self.network.netmask}")
        print("-" * 50)
    
    def calculate_subnets(self, num_subnets: int) -> List[ipaddress.IPv4Network]:
        """
        Divide the network into specified number of equal subnets
        """
        try:
            # Calculate new prefix length
            import math
            bits_needed = math.ceil(math.log2(num_subnets))
            new_prefix = self.network.prefixlen + bits_needed
            
            if new_prefix > 30:
                raise ValueError("Too many subnets requested. Maximum is limited by network size.")
            
            subnets = list(self.network.subnets(new_prefix=new_prefix))
            
            print(f"\n✅ Created {len(subnets)} subnets with /{new_prefix} prefix:")
            for idx, subnet in enumerate(subnets[:num_subnets], 1):
                print(f"  Subnet {idx}: {subnet} | Usable Hosts: {subnet.num_addresses - 2}")
            
            return subnets[:num_subnets]
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def vlsm_allocation(self, requirements: list) -> list:
        """
        Allocate subnets based on variable length subnet masking (VLSM)
        requirements: List of required host counts for each subnet
        """
        import ipaddress
        import math
        sorted_reqs = sorted(requirements, reverse=True)
        allocations = []
        available_start = int(self.network.network_address)
        available_end = int(self.network.broadcast_address)
    
        print(f"\n🔧 VLSM Allocation for requirements: {requirements}")
        print("=" * 60)
    
        for idx, hosts_needed in enumerate(sorted_reqs, 1):
            total_needed = hosts_needed + 2
            host_bits = math.ceil(math.log2(total_needed))
            new_prefix = 32 - host_bits
            subnet_size = 2 ** host_bits
            subnet_network = available_start
            subnet_broadcast = available_start + subnet_size - 1
        
            if subnet_broadcast > available_end:
                print(f"❌ Cannot allocate subnet {idx}: Insufficient space.")
                break
        
            allocation = {
            'subnet_id': idx,
            'required_hosts': hosts_needed,
            'subnet': f"{ipaddress.IPv4Address(subnet_network)}/{new_prefix}",
            'usable_hosts': subnet_size - 2,
            'network_address': str(ipaddress.IPv4Address(subnet_network)),
            'broadcast_address': str(ipaddress.IPv4Address(subnet_broadcast)),
            'first_usable': str(ipaddress.IPv4Address(subnet_network + 1)),
            'last_usable': str(ipaddress.IPv4Address(subnet_broadcast - 1)),
            'netmask': str(ipaddress.IPv4Network(f"{ipaddress.IPv4Address(subnet_network)}/{new_prefix}").netmask)
            }
        
            allocations.append(allocation)
        
            print(f"\n📦 Subnet {idx}:")
            print(f"   Required: {hosts_needed} hosts | Allocated: {allocation['usable_hosts']} hosts")
            print(f"   Network: {allocation['subnet']}")
            print(f"   Range: {allocation['first_usable']} - {allocation['last_usable']}")
        
        # Update available_start for next round
            available_start = subnet_broadcast + 1
    
        print("\n" + "=" * 60)
        print(f"✅ Successfully allocated {len(allocations)} subnets")
    
        return allocations
    
    def check_ip_conflict(self, ip_list: List[str]) -> Dict:
        """
        Check for duplicate IPs in the list
        """
        from collections import Counter
        
        conflicts = []
        ip_count = Counter(ip_list)
        
        for ip, count in ip_count.items():
            if count > 1:
                conflicts.append({'ip': ip, 'occurrences': count})
        
        result = {
            'total_ips': len(ip_list),
            'unique_ips': len(ip_count),
            'conflicts_found': len(conflicts),
            'conflicts': conflicts
        }
        
        if conflicts:
            print(f"\n⚠️  IP CONFLICTS DETECTED!")
            for conflict in conflicts:
                print(f"   {conflict['ip']} appears {conflict['occurrences']} times")
        else:
            print(f"\n✅ No conflicts found in {len(ip_list)} IP addresses")
        
        return result
    
    def ip_in_subnet(self, ip: str, subnet: str) -> bool:
        """
        Check if an IP address belongs to a subnet
        """
        ip_obj = ipaddress.IPv4Address(ip)
        subnet_obj = ipaddress.IPv4Network(subnet, strict=False)
        
        return ip_obj in subnet_obj


# Test the calculator
if __name__ == "__main__":
    print("=" * 60)
    print("    SMARTSUBNET AI - SUBNET CALCULATOR v1.0")
    print("=" * 60)
    
    # Example 1: Basic subnet division
    print("\n📊 EXAMPLE 1: Divide network into equal subnets")
    calc = SubnetCalculator("10.0.0.0/16")
    calc.calculate_subnets(4)
    
    # Example 2: VLSM allocation
    print("\n\n📊 EXAMPLE 2: VLSM Allocation")
    calc2 = SubnetCalculator("192.168.1.0/24")
    vlsm_result = calc2.vlsm_allocation([50, 100, 25, 10])
    
    # Example 3: IP conflict detection
    print("\n\n📊 EXAMPLE 3: IP Conflict Detection")
    test_ips = [
        "192.168.1.10",
        "192.168.1.20",
        "192.168.1.10",  # Duplicate
        "192.168.1.30",
        "192.168.1.20",  # Duplicate
    ]
    calc3 = SubnetCalculator("192.168.1.0/24")
    calc3.check_ip_conflict(test_ips)
    
    # Example 4: Check IP membership
    print("\n\n📊 EXAMPLE 4: IP Subnet Membership")
    calc4 = SubnetCalculator("10.0.0.0/8")
    test_ip = "10.50.100.5"
    test_subnet = "10.50.0.0/16"
    result = calc4.ip_in_subnet(test_ip, test_subnet)
    print(f"\nIs {test_ip} in {test_subnet}? {result}")
