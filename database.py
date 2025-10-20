from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class SubnetAllocation(Base):
    """Store subnet allocation history"""
    __tablename__ = 'subnet_allocations'
    
    id = Column(Integer, primary_key=True)
    subnet = Column(String(50), nullable=False)
    total_ips = Column(Integer)
    allocated_ips = Column(Integer)
    available_ips = Column(Integer)
    utilization_percent = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    department = Column(String(100))
    
    def __repr__(self):
        return f"<Subnet {self.subnet} | {self.utilization_percent}% utilized>"


class IPConflict(Base):
    """Log IP conflicts detected"""
    __tablename__ = 'ip_conflicts'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(15), nullable=False)
    subnet = Column(String(50))
    conflict_type = Column(String(50))  # duplicate, unauthorized, etc.
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_method = Column(String(100))
    
    def __repr__(self):
        status = "RESOLVED" if self.resolved else "ACTIVE"
        return f"<Conflict {self.ip_address} | {status}>"


class PredictionLog(Base):
    """Store ML prediction results"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    subnet = Column(String(50), nullable=False)
    prediction_date = Column(DateTime, default=datetime.utcnow)
    forecast_days = Column(Integer)  # 7, 30, or 90
    predicted_utilization = Column(Float)
    confidence_score = Column(Float)
    actual_utilization = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<Prediction {self.subnet} | {self.forecast_days}d | {self.predicted_utilization}%>"


class NetworkDevice(Base):
    """Track network devices"""
    __tablename__ = 'network_devices'
    
    id = Column(Integer, primary_key=True)
    device_name = Column(String(100))
    ip_address = Column(String(15))
    device_type = Column(String(50))  # router, switch, server, etc.
    subnet = Column(String(50))
    mac_address = Column(String(17))
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # active, inactive, quarantined
    
    def __repr__(self):
        return f"<Device {self.device_name} | {self.ip_address}>"


class DatabaseManager:
    """Manage database operations"""
    
    def __init__(self, db_path='smartsubnet.db'):
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        print(f"✅ Database initialized: {db_path}")
    
    def add_subnet_allocation(self, subnet, total, allocated, department="Default"):
        """Add subnet allocation record"""
        available = total - allocated
        utilization = (allocated / total * 100) if total > 0 else 0
        
        record = SubnetAllocation(
            subnet=subnet,
            total_ips=total,
            allocated_ips=allocated,
            available_ips=available,
            utilization_percent=round(utilization, 2),
            department=department
        )
        
        self.session.add(record)
        self.session.commit()
        print(f"✅ Added allocation: {subnet} | {utilization:.2f}% utilized")
        return record
    
    def log_conflict(self, ip, subnet, conflict_type):
        """Log an IP conflict"""
        conflict = IPConflict(
            ip_address=ip,
            subnet=subnet,
            conflict_type=conflict_type
        )
        
        self.session.add(conflict)
        self.session.commit()
        print(f"⚠️  Conflict logged: {ip} in {subnet} | Type: {conflict_type}")
        return conflict
    
    def resolve_conflict(self, conflict_id, method):
        """Mark conflict as resolved"""
        conflict = self.session.query(IPConflict).filter_by(id=conflict_id).first()
        if conflict:
            conflict.resolved = True
            conflict.resolved_at = datetime.utcnow()
            conflict.resolution_method = method
            self.session.commit()
            print(f"✅ Conflict {conflict_id} resolved via {method}")
            return True
        return False
    
    def add_device(self, name, ip, device_type, subnet, mac="00:00:00:00:00:00"):
        """Add network device"""
        device = NetworkDevice(
            device_name=name,
            ip_address=ip,
            device_type=device_type,
            subnet=subnet,
            mac_address=mac,
            status="active"
        )
        
        self.session.add(device)
        self.session.commit()
        print(f"✅ Device added: {name} ({ip})")
        return device
    
    def get_subnet_utilization(self, subnet=None):
        """Get utilization statistics"""
        query = self.session.query(SubnetAllocation)
        if subnet:
            query = query.filter_by(subnet=subnet)
        
        return query.order_by(SubnetAllocation.timestamp.desc()).all()
    
    def get_active_conflicts(self):
        """Get all unresolved conflicts"""
        return self.session.query(IPConflict).filter_by(resolved=False).all()
    
    def get_devices_by_subnet(self, subnet):
        """Get all devices in a subnet"""
        return self.session.query(NetworkDevice).filter_by(subnet=subnet).all()
    
    def close(self):
        """Close database connection"""
        self.session.close()
        print("Database connection closed")


# Test database
if __name__ == "__main__":
    print("="*60)
    print("    DATABASE MANAGER TEST")
    print("="*60 + "\n")
    
    # Initialize database
    db = DatabaseManager('test_smartsubnet.db')
    
    # Add some sample data
    print("\n📝 Adding subnet allocations...")
    db.add_subnet_allocation("192.168.1.0/24", 254, 100, "Engineering")
    db.add_subnet_allocation("192.168.2.0/24", 254, 200, "Sales")
    db.add_subnet_allocation("10.0.1.0/24", 254, 50, "Management")
    
    print("\n📝 Adding devices...")
    db.add_device("Server-01", "192.168.1.10", "server", "192.168.1.0/24")
    db.add_device("Router-01", "192.168.1.1", "router", "192.168.1.0/24")
    db.add_device("Switch-01", "192.168.1.2", "switch", "192.168.1.0/24")
    
    print("\n📝 Logging conflicts...")
    db.log_conflict("192.168.1.10", "192.168.1.0/24", "duplicate")
    db.log_conflict("192.168.2.50", "192.168.2.0/24", "unauthorized")
    
    print("\n📊 Retrieving utilization data...")
    utilizations = db.get_subnet_utilization()
    for util in utilizations:
        print(f"  {util}")
    
    print("\n📊 Active conflicts:")
    conflicts = db.get_active_conflicts()
    for conflict in conflicts:
        print(f"  {conflict}")
    
    print("\n📊 Devices in 192.168.1.0/24:")
    devices = db.get_devices_by_subnet("192.168.1.0/24")
    for device in devices:
        print(f"  {device}")
    
    # Resolve a conflict
    print("\n🔧 Resolving conflict ID 1...")
    db.resolve_conflict(1, "IP reassignment")
    
    db.close()
