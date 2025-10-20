import ipaddress
import re

class IPValidator:
    """
    Validates IP addresses and performs various checks
    """
    
    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """Check if string is a valid IPv4 address"""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except:
            return False
    
    @staticmethod
    def is_valid_cidr(cidr: str) -> bool:
        """Check if string is valid CIDR notation"""
        try:
            ipaddress.IPv4Network(cidr, strict=False)
            return True
        except:
            return False
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP is in private range"""
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            return ip_obj.is_private
        except:
            return False
    
    @staticmethod
    def get_ip_class(ip: str) -> str:
        """Determine IP address class (A, B, C, D, E)"""
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            first_octet = int(str(ip_obj).split('.')[0])
            
            if first_octet >= 1 and first_octet <= 126:
                return "Class A"
            elif first_octet >= 128 and first_octet <= 191:
                return "Class B"
            elif first_octet >= 192 and first_octet <= 223:
                return "Class C"
            elif first_octet >= 224 and first_octet <= 239:
                return "Class D (Multicast)"
            else:
                return "Class E (Reserved)"
        except:
            return "Invalid IP"
    
    @staticmethod
    def validate_ip_list(ip_list: list) -> dict:
        """Validate a list of IPs and return statistics"""
        valid = []
        invalid = []
        private = []
        public = []
        
        for ip in ip_list:
            if IPValidator.is_valid_ipv4(ip):
                valid.append(ip)
                if IPValidator.is_private_ip(ip):
                    private.append(ip)
                else:
                    public.append(ip)
            else:
                invalid.append(ip)
        
        return {
            'total': len(ip_list),
            'valid': len(valid),
            'invalid': len(invalid),
            'private': len(private),
            'public': len(public),
            'invalid_ips': invalid
        }


# Test validator
if __name__ == "__main__":
    print("🔍 IP VALIDATOR TEST\n")
    
    validator = IPValidator()
    
    # Test IPs
    test_ips = [
        "192.168.1.1",
        "10.0.0.1",
        "8.8.8.8",
        "256.1.1.1",  # Invalid
        "172.16.0.1",
        "invalid_ip"  # Invalid
    ]
    
    print("Testing individual IPs:")
    for ip in test_ips:
        valid = validator.is_valid_ipv4(ip)
        if valid:
            is_private = validator.is_private_ip(ip)
            ip_class = validator.get_ip_class(ip)
            print(f"✅ {ip:20s} | Private: {is_private} | {ip_class}")
        else:
            print(f"❌ {ip:20s} | INVALID")
    
    print("\n" + "="*50)
    print("\nBatch validation statistics:")
    stats = validator.validate_ip_list(test_ips)
    for key, value in stats.items():
        if key != 'invalid_ips':
            print(f"  {key}: {value}")
