import random
import time
from datetime import datetime, timedelta
from database import DatabaseManager, SubnetAllocation  # ✅ FIX: import here
import ipaddress

class NetworkDataCollector:
    """
    Simulates data collection from network devices
    In production, this would connect to real SDN APIs, DHCP servers, etc.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.subnets = [
            "192.168.1.0/24",
            "192.168.2.0/24",
            "10.0.1.0/24",
            "10.0.2.0/24",
            "172.16.1.0/24"
        ]
        print("📡 Network Data Collector initialized")
    
    def simulate_subnet_usage(self, subnet_str):
        """Simulate IP allocation in a subnet"""
        subnet = ipaddress.IPv4Network(subnet_str)
        total_ips = subnet.num_addresses - 2  # Exclude network and broadcast
        
        # Simulate random allocation between 10% and 90%
        allocated = random.randint(int(total_ips * 0.1), int(total_ips * 0.9))
        
        return total_ips, allocated
    
    def collect_snapshot(self):
        """Collect current network state snapshot"""
        print(f"\n📸 Collecting network snapshot at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        departments = ["Engineering", "Sales", "HR", "IT", "Management"]
        
        for subnet in self.subnets:
            total, allocated = self.simulate_subnet_usage(subnet)
            dept = random.choice(departments)
            
            self.db.add_subnet_allocation(subnet, total, allocated, dept)
        
        # Simulate occasional conflicts
        if random.random() < 0.3:  # 30% chance of conflict
            conflict_subnet = random.choice(self.subnets)
            network = ipaddress.IPv4Network(conflict_subnet)
            conflict_ip = str(network.network_address + random.randint(1, 100))
            conflict_type = random.choice(["duplicate", "unauthorized", "expired_lease"])
            
            self.db.log_conflict(conflict_ip, conflict_subnet, conflict_type)
    
    def collect_continuous(self, duration_minutes=5, interval_seconds=30):
        """Collect data continuously for specified duration"""
        print(f"\n🔄 Starting continuous collection for {duration_minutes} minutes")
        print(f"   Snapshot interval: {interval_seconds} seconds")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        snapshot_count = 0
        
        while datetime.now() < end_time:
            snapshot_count += 1
            self.collect_snapshot()
            
            remaining = (end_time - datetime.now()).total_seconds()
            if remaining > 0:
                wait_time = min(interval_seconds, remaining)
                print(f"   ⏳ Waiting {wait_time:.0f}s... (Snapshot {snapshot_count} complete)")
                time.sleep(wait_time)
        
        print(f"\n✅ Collection complete! Total snapshots: {snapshot_count}")
    
    def generate_historical_data(self, days=30):
        """Generate historical data for ML training"""
        print(f"\n📚 Generating {days} days of historical data...")
        
        for day in range(days, 0, -1):
            for hour in [0, 6, 12, 18]:  # 4 times per day
                # Simulate growth trend
                growth_factor = 1 + (days - day) * 0.01  # 1% daily growth
                
                for subnet in self.subnets:
                    subnet_obj = ipaddress.IPv4Network(subnet)
                    total_ips = subnet_obj.num_addresses - 2
                    
                    # Base allocation with growth and hourly variation
                    base_allocated = int(total_ips * 0.3 * growth_factor)
                    hourly_variation = random.randint(-20, 20)
                    allocated = max(10, min(total_ips, base_allocated + hourly_variation))
                    
                    # Create record with past timestamp
                    past_time = datetime.now() - timedelta(days=day, hours=(24-hour))
                
                    
                    # Direct insertion with custom timestamp
                    historical_record = SubnetAllocation(
                        subnet=subnet,
                        total_ips=total_ips,
                        allocated_ips=allocated,
                        available_ips=total_ips - allocated,
                        utilization_percent=round((allocated / total_ips * 100), 2),
                        timestamp=past_time,
                        department=random.choice(["Engineering", "Sales", "IT"])
                    )
                    
                    self.db.session.add(historical_record)
        
        self.db.session.commit()
        print(f"✅ Generated {days * 4 * len(self.subnets)} historical records")


# Test data collector
if __name__ == "__main__":
    print("="*60)
    print("    NETWORK DATA COLLECTOR TEST")
    print("="*60)
    
    # Initialize
    db = DatabaseManager('smartsubnet.db')
    collector = NetworkDataCollector(db)
    
    # Generate historical data for training
    collector.generate_historical_data(days=30)
    
    # Collect a few real-time snapshots
    print("\n" + "="*60)
    print("Testing real-time collection...")
    print("="*60)
    collector.collect_continuous(duration_minutes=2, interval_seconds=20)
    
    # Show statistics
    print("\n📊 Database Statistics:")
    from sqlalchemy import func
    from database import SubnetAllocation, IPConflict
    
    total_records = db.session.query(func.count(SubnetAllocation.id)).scalar()
    total_conflicts = db.session.query(func.count(IPConflict.id)).scalar()
    
    print(f"   Total allocation records: {total_records}")
    print(f"   Total conflicts logged: {total_conflicts}")
    
    db.close()
