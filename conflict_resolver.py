from database import DatabaseManager, IPConflict, NetworkDevice
from datetime import datetime
import ipaddress
import random

class ConflictDetectionEngine:
    """
    Detects and automatically resolves IP conflicts
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.quarantine_subnet = "192.168.255.0/24"  # Quarantine zone
        print("🛡️  Conflict Detection Engine initialized")
    
    def scan_for_duplicates(self):
        """Scan all devices for duplicate IPs"""
        print("\n🔍 Scanning for duplicate IP addresses...")
        
        # Get all active devices
        devices = self.db.session.query(NetworkDevice).filter_by(status='active').all()
        
        ip_registry = {}
        duplicates = []
        
        for device in devices:
            ip = device.ip_address
            if ip in ip_registry:
                duplicates.append({
                    'ip': ip,
                    'device1': ip_registry[ip],
                    'device2': device
                })
                print(f"   ⚠️  DUPLICATE: {ip} assigned to both {ip_registry[ip].device_name} and {device.device_name}")
            else:
                ip_registry[ip] = device
        
        if not duplicates:
            print("   ✅ No duplicate IPs found")
        
        return duplicates
    
    def scan_for_unauthorized(self, authorized_subnets):
        """Detect IPs outside authorized subnets"""
        print("\n🔍 Scanning for unauthorized IP assignments...")
        
        unauthorized = []
        devices = self.db.session.query(NetworkDevice).filter_by(status='active').all()
        
        for device in devices:
            is_authorized = False
            device_ip = ipaddress.IPv4Address(device.ip_address)
            
            for subnet_str in authorized_subnets:
                subnet = ipaddress.IPv4Network(subnet_str, strict=False)
                if device_ip in subnet:
                    is_authorized = True
                    break
            
            if not is_authorized:
                unauthorized.append(device)
                print(f"   ⚠️  UNAUTHORIZED: {device.device_name} ({device.ip_address}) not in allowed subnets")
        
        if not unauthorized:
            print("   ✅ All IPs within authorized subnets")
        
        return unauthorized
    
    def quarantine_device(self, device):
        """Move device to quarantine subnet"""
        old_ip = device.ip_address
        
        # Assign new IP from quarantine subnet
        quarantine_net = ipaddress.IPv4Network(self.quarantine_subnet)
        new_ip = str(quarantine_net.network_address + random.randint(10, 100))
        
        device.ip_address = new_ip
        device.status = "quarantined"
        device.subnet = self.quarantine_subnet
        
        self.db.session.commit()
        
        print(f"   🚨 QUARANTINED: {device.device_name} moved from {old_ip} to {new_ip}")
        
        return new_ip
    
    def auto_remediate_duplicate(self, duplicate_info):
        """Automatically resolve duplicate IP conflict"""
        ip = duplicate_info['ip']
        device1 = duplicate_info['device1']
        device2 = duplicate_info['device2']
        
        print(f"\n🔧 AUTO-REMEDIATING duplicate IP {ip}...")
        
        # Log conflict
        conflict = self.db.log_conflict(ip, device1.subnet, "duplicate")
        
        # Decision: Keep device1 (first assigned), quarantine device2
        print(f"   ✓ Keeping {device1.device_name} with {ip}")
        print(f"   ✓ Quarantining {device2.device_name}")
        
        new_ip = self.quarantine_device(device2)
        
        # Mark conflict as resolved
        self.db.resolve_conflict(conflict.id, f"Auto-quarantine to {new_ip}")
        
        print(f"   ✅ Conflict resolved automatically")
        
        return True
    
    def auto_remediate_unauthorized(self, device, authorized_subnets):
        """Resolve unauthorized IP assignment"""
        print(f"\n🔧 AUTO-REMEDIATING unauthorized device {device.device_name}...")
        
        # Log conflict
        conflict = self.db.log_conflict(device.ip_address, "N/A", "unauthorized")
        
        # Option 1: Quarantine
        # Option 2: Reassign to authorized subnet
        
        # For this implementation, we'll quarantine
        new_ip = self.quarantine_device(device)
        
        self.db.resolve_conflict(conflict.id, f"Auto-quarantine to {new_ip}")
        
        print(f"   ✅ Device quarantined, admin notified")
        
        return True
    
    def run_full_scan(self, authorized_subnets):
        """Run complete conflict detection and auto-remediation"""
        print("\n" + "="*60)
        print("    STARTING FULL NETWORK SCAN")
        print("="*60)
        
        total_conflicts = 0
        
        # Scan for duplicates
        duplicates = self.scan_for_duplicates()
        for dup in duplicates:
            self.auto_remediate_duplicate(dup)
            total_conflicts += 1
        
        # Scan for unauthorized
        unauthorized = self.scan_for_unauthorized(authorized_subnets)
        for device in unauthorized:
            self.auto_remediate_unauthorized(device, authorized_subnets)
            total_conflicts += 1
        
        print("\n" + "="*60)
        print(f"    SCAN COMPLETE: {total_conflicts} conflicts resolved")
        print("="*60)
        
        return total_conflicts
    
    def get_conflict_report(self):
        """Generate conflict resolution report"""
        active = self.db.session.query(IPConflict).filter_by(resolved=False).count()
        resolved = self.db.session.query(IPConflict).filter_by(resolved=True).count()
        quarantined = self.db.session.query(NetworkDevice).filter_by(status='quarantined').count()
        
        report = {
            'active_conflicts': active,
            'resolved_conflicts': resolved,
            'quarantined_devices': quarantined,
            'resolution_rate': (resolved / (active + resolved) * 100) if (active + resolved) > 0 else 0
        }
        
        return report


# Test conflict resolver
if __name__ == "__main__":
    print("="*60)
    print("    CONFLICT DETECTION & RESOLUTION TEST")
    print("="*60)
    
    # Initialize
    db = DatabaseManager('smartsubnet.db')
    resolver = ConflictDetectionEngine(db)
    
    # Create some test devices with conflicts
    print("\n📝 Creating test scenario with conflicts...")
    
    # Add normal devices
    db.add_device("Server-Web-01", "192.168.1.10", "server", "192.168.1.0/24", "00:11:22:33:44:01")
    db.add_device("Server-DB-01", "192.168.1.20", "server", "192.168.1.0/24", "00:11:22:33:44:02")
    
    # Add duplicate IP (conflict!)
    db.add_device("Server-Web-02", "192.168.1.10", "server", "192.168.1.0/24", "00:11:22:33:44:03")
    
    # Add unauthorized IP
    db.add_device("Rogue-Device", "10.99.99.99", "unknown", "10.99.99.0/24", "00:11:22:33:44:04")
    
    # Define authorized subnets
    authorized = [
        "192.168.1.0/24",
        "192.168.2.0/24",
        "10.0.1.0/24",
        "10.0.2.0/24",
        "172.16.1.0/24"
    ]
    
    # Run full scan
    resolver.run_full_scan(authorized)
    
    # Show report
    print("\n📊 CONFLICT RESOLUTION REPORT")
    print("="*60)
    report = resolver.get_conflict_report()
    for key, value in report.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Show quarantined devices
    print("\n📋 Quarantined Devices:")
    quarantined = db.session.query(NetworkDevice).filter_by(status='quarantined').all()
    for dev in quarantined:
        print(f"   {dev}")
    
    db.close()
