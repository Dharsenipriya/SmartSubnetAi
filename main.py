#!/usr/bin/env python3
"""
SmartSubnet AI - Main Orchestration Script
"""

import time
import schedule
from datetime import datetime
from database import DatabaseManager
from data_collector import NetworkDataCollector
from ml_predictor import SubnetDemandPredictor
from conflict_resolver import ConflictDetectionEngine

class SmartSubnetAI:
    """
    Main orchestration system
    """
    
    def __init__(self):
        print("="*70)
        print("    🌐 SMARTSUBNET AI - INITIALIZING")
        print("="*70)
        
        self.db = DatabaseManager('smartsubnet.db')
        self.collector = NetworkDataCollector(self.db)
        self.predictor = SubnetDemandPredictor(self.db)
        self.resolver = ConflictDetectionEngine(self.db)
        
        self.authorized_subnets = [
            "192.168.1.0/24",
            "192.168.2.0/24",
            "10.0.1.0/24",
            "10.0.2.0/24",
            "172.16.1.0/24"
        ]
        
        print("\n✅ All systems initialized successfully")
    
    def collect_data(self):
        """Scheduled data collection"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📡 Running data collection...")
        self.collector.collect_snapshot()
    
    def run_conflict_scan(self):
        """Scheduled conflict detection"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Running conflict scan...")
        self.resolver.run_full_scan(self.authorized_subnets)
    
    def generate_predictions(self):
        """Scheduled ML predictions"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🤖 Generating ML predictions...")
        self.predictor.predict_all_subnets(days_ahead=7)
    
    def daily_report(self):
        """Generate daily summary report"""
        print("\n" + "="*70)
        print(f"    📊 DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*70)
        
        # Conflict stats
        report = self.resolver.get_conflict_report()
        print(f"\n🛡️  Conflicts:")
        print(f"   Active: {report['active_conflicts']}")
        print(f"   Resolved: {report['resolved_conflicts']}")
        print(f"   Resolution Rate: {report['resolution_rate']:.1f}%")
        
        # Utilization stats
        from database import SubnetAllocation
        latest = self.db.session.query(SubnetAllocation).order_by(
            SubnetAllocation.timestamp.desc()
        ).limit(5).all()
        
        if latest:
            avg_util = sum([a.utilization_percent for a in latest]) / len(latest)
            print(f"\n📊 Network Utilization:")
            print(f"   Average: {avg_util:.1f}%")
            for alloc in latest:
                print(f"   {alloc.subnet}: {alloc.utilization_percent:.1f}%")
        
        print("\n" + "="*70)
    
    def run_continuous(self):
        """Run continuous monitoring"""
        print("\n🚀 Starting continuous monitoring mode...")
        print("   Data collection: Every 5 minutes")
        print("   Conflict scan: Every 15 minutes")
        print("   ML predictions: Every 6 hours")
        print("   Daily report: 9:00 AM daily")
        print("\n   Press Ctrl+C to stop")
        
        # Schedule tasks
        schedule.every(5).minutes.do(self.collect_data)
        schedule.every(15).minutes.do(self.run_conflict_scan)
        schedule.every(6).hours.do(self.generate_predictions)
        schedule.every().day.at("09:00").do(self.daily_report)
        
        # Run immediately once
        self.collect_data()
        self.run_conflict_scan()
        self.generate_predictions()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n⏸️  Stopping SmartSubnet AI...")
            self.db.close()
            print("✅ Shutdown complete")
    
    def run_demo(self):
        """Run demonstration mode"""
        print("\n🎬 Running demonstration mode...\n")
        
        print("Step 1: Collecting network data...")
        self.collector.collect_snapshot()
        time.sleep(2)
        
        print("\nStep 2: Scanning for conflicts...")
        self.run_conflict_scan()
        time.sleep(2)
        
        print("\nStep 3: Generating ML predictions...")
        self.generate_predictions()
        time.sleep(2)
        
        print("\nStep 4: Daily report...")
        self.daily_report()
        
        print("\n✅ Demo complete! Run 'streamlit run dashboard.py' to view results")


if __name__ == "__main__":
    import sys
    
    system = SmartSubnetAI()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            system.run_continuous()
        elif sys.argv[1] == "--demo":
            system.run_demo()
        else:
            print("Usage: python main.py [--continuous|--demo]")
    else:
        # Default: run demo
        system.run_demo()
