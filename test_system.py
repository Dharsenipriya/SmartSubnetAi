import pytest
from subnet_calculator import SubnetCalculator
from ip_validator import IPValidator
from database import DatabaseManager
import os


def test_subnet_calculator():
    """Test subnet calculator"""
    calc = SubnetCalculator("192.168.1.0/24")
    subnets = calc.calculate_subnets(4)
    assert len(subnets) == 4
    print("✅ Subnet calculator test passed")


def test_vlsm():
    """Test VLSM allocation"""
    calc = SubnetCalculator("10.0.0.0/16")
    allocations = calc.vlsm_allocation([100, 50, 25])
    assert len(allocations) == 3
    assert allocations[0]['required_hosts'] == 100
    print("✅ VLSM test passed")


def test_ip_validator():
    """Test IP validator"""
    assert IPValidator.is_valid_ipv4("192.168.1.1") == True
    assert IPValidator.is_valid_ipv4("999.999.999.999") == False
    assert IPValidator.is_private_ip("192.168.1.1") == True
    assert IPValidator.is_private_ip("8.8.8.8") == False
    print("✅ IP validator test passed")


def test_database():
    """Test database operations"""
    # Use test database
    db = DatabaseManager('test.db')
    
    # Test subnet allocation
    record = db.add_subnet_allocation("192.168.1.0/24", 254, 100, "Test")
    assert record.utilization_percent > 0
    
    # Test conflict logging
    conflict = db.log_conflict("192.168.1.1", "192.168.1.0/24", "test")
    assert conflict.resolved == False
    
    # Test conflict resolution
    success = db.resolve_conflict(conflict.id, "test resolution")
    assert success == True
    
    db.close()
    os.remove('test.db')
    print("✅ Database test passed")


def test_conflict_detection():
    """Test conflict detection"""
    db = DatabaseManager('test.db')
    
    # Add devices with duplicate IP
    db.add_device("Device1", "192.168.1.10", "server", "192.168.1.0/24")
    db.add_device("Device2", "192.168.1.10", "server", "192.168.1.0/24")
    
    from conflict_resolver import ConflictDetectionEngine
    resolver = ConflictDetectionEngine(db)
    
    duplicates = resolver.scan_for_duplicates()
    assert len(duplicates) > 0
    
    db.close()
    os.remove('test.db')
    print("✅ Conflict detection test passed")


if __name__ == "__main__":
    print("="*60)
    print("    RUNNING SYSTEM TESTS")
    print("="*60 + "\n")
    
    test_subnet_calculator()
    test_vlsm()
    test_ip_validator()
    test_database()
    test_conflict_detection()
    
    print("\n" + "="*60)
    print("    ✅ ALL TESTS PASSED!")
    print("="*60)
