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
    
    def vlsm_allocation(self, requirements: List[int]) -> List[Dict]:
        """
        Variable Length Subnet Masking - allocate subnets based on host requirements
        Requirements: List of host counts needed (e.g., [50, 100, 25, 10])
        """
        # Sort requirements in descending order
        sorted_reqs = sorted(requirements, reverse=True)
        allocations = []
        available_network = self.network
        
        print(f"\n🔧 VLSM Allocation for requirements: {requirements}")
        print("=" * 60)
        
        for idx, hosts_needed in enumerate(sorted_reqs, 1):
            # Calculate required prefix length
            import math
            # Add 2 for network and broadcast addresses
            total_needed = hosts_needed + 2
            host_bits = math.ceil(math.log2(total_needed))
            new_prefix = 32 - host_bits
            
            # Create subnet
            try:
                subnet = ipaddress.IPv4Network(f"{available_network.network_address}/{new_prefix}", strict=False)
                
                # Ensure subnet fits within available network
                if subnet.network_address < available_network.network_address or \
                   subnet.broadcast_address > available_network.broadcast_address:
                    print(f"❌ Cannot allocate subnet {idx}: Insufficient space")
                    break
                
                allocation = {
                    'subnet_id': idx,
                    'required_hosts': hosts_needed,
                    'subnet': str(subnet),
                    'usable_hosts': subnet.num_addresses - 2,
                    'network_address': str(subnet.network_address),
                    'broadcast_address': str(subnet.broadcast_address),
                    'first_usable': str(subnet.network_address + 1),
                    'last_usable': str(subnet.broadcast_address - 1),
                    'netmask': str(subnet.netmask)
                }
                
                allocations.append(allocation)
                
                print(f"\n📦 Subnet {idx}:")
                print(f"   Required: {hosts_needed} hosts | Allocated: {allocation['usable_hosts']} hosts")
                print(f"   Network: {allocation['subnet']}")
                print(f"   Range: {allocation['first_usable']} - {allocation['last_usable']}")
                
                # Move to next available address
                next_address = subnet.broadcast_address + 1
                if next_address <= available_network.broadcast_address:
                    remaining = available_network.broadcast_address - next_address + 1
                    available_network = ipaddress.IPv4Network(
                        f"{next_address}/{32 - (remaining - 1).bit_length()}", 
                        strict=False
                    )
                else:
                    break
                    
            except Exception as e:
                print(f"❌ Error allocating subnet {idx}: {e}")
                break
        
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
