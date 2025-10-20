#!/usr/bin/env python3
"""
SmartSubnet AI - Main Orchestration Script with Integrated Alerts
"""

import time
import schedule
from datetime import datetime
from database import DatabaseManager
from data_collector import NetworkDataCollector
from ml_predictor import SubnetDemandPredictor
from conflict_resolver import ConflictDetectionEngine
from alert_manager import AlertManager

class SmartSubnetAI:
    """
    Main orchestration system with integrated alert management
    """
    
    def __init__(self):
        print("="*70)
        print("    🌐 SMARTSUBNET AI - INITIALIZING")
        print("="*70)
        
        self.db = DatabaseManager('smartsubnet.db')
        self.collector = NetworkDataCollector(self.db)
        self.predictor = SubnetDemandPredictor(self.db)
        self.resolver = ConflictDetectionEngine(self.db)
        self.alert_manager = AlertManager(self.db)  # NEW: Alert system
        
        self.authorized_subnets = [
            "192.168.1.0/24",
            "192.168.2.0/24",
            "10.0.1.0/24",
            "10.0.2.0/24",
            "172.16.1.0/24"
        ]
        
        print("\n✅ All systems initialized successfully")
        print("   📡 Data Collector: Ready")
        print("   🤖 ML Predictor: Ready")
        print("   🛡️  Conflict Resolver: Ready")
        print("   📧 Alert Manager: Ready")
    
    def collect_data(self):
        """Scheduled data collection"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📡 Running data collection...")
        self.collector.collect_snapshot()
    
    def run_conflict_scan(self):
        """Scheduled conflict detection with alerts"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Running conflict scan...")
        conflicts_found = self.resolver.run_full_scan(self.authorized_subnets)
        
        # Check and send alerts if conflicts found
        if conflicts_found > 0:
            self.alert_manager.check_conflict_alerts()
    
    def generate_predictions(self):
        """Scheduled ML predictions with alerts"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🤖 Generating ML predictions...")
        predictions = self.predictor.predict_all_subnets(days_ahead=7)
        
        # Check prediction-based alerts
        if predictions:
            self.alert_manager.check_prediction_alerts(predictions)
    
    def check_utilization_alerts(self):
        """Check for high utilization and send alerts"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📊 Checking utilization alerts...")
        self.alert_manager.check_utilization_alerts()
    
    def generate_daily_report(self):
        """Generate and send daily summary report"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📊 Generating daily report...")
        self.alert_manager.generate_daily_report()
    
    def daily_report(self):
        """Generate daily summary report (legacy - calls new method)"""
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
        
        # Also send via alert system
        self.generate_daily_report()
    
    def run_continuous(self):
        """Run continuous monitoring with alerts"""
        print("\n🚀 Starting continuous monitoring mode...")
        print("   📡 Data collection: Every 5 minutes")
        print("   🔍 Conflict scan: Every 15 minutes")
        print("   🤖 ML predictions: Every 6 hours")
        print("   📊 Utilization alerts: Every 30 minutes")
        print("   📧 Daily report: 9:00 AM daily")
        print("\n   Press Ctrl+C to stop")
        
        # Schedule tasks
        schedule.every(5).minutes.do(self.collect_data)
        schedule.every(15).minutes.do(self.run_conflict_scan)
        schedule.every(6).hours.do(self.generate_predictions)
        schedule.every(30).minutes.do(self.check_utilization_alerts)
        schedule.every().day.at("09:00").do(self.daily_report)
        
        # Run immediately once
        print("\n🎬 Running initial checks...")
        self.collect_data()
        self.run_conflict_scan()
        self.generate_predictions()
        self.check_utilization_alerts()
        
        print("\n✅ Initial checks complete. Entering scheduled mode...\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n⏸️  Stopping SmartSubnet AI...")
            self.db.close()
            print("✅ Shutdown complete")
    
    def run_demo(self):
        """Run demonstration mode with alerts"""
        print("\n🎬 Running demonstration mode...\n")
        
        print("Step 1: Collecting network data...")
        self.collector.collect_snapshot()
        time.sleep(2)
        
        print("\nStep 2: Scanning for conflicts...")
        self.run_conflict_scan()
        time.sleep(2)
        
        print("\nStep 3: Generating ML predictions...")
        predictions = self.predictor.predict_all_subnets(days_ahead=7)
        time.sleep(2)
        
        print("\nStep 4: Checking utilization alerts...")
        self.check_utilization_alerts()
        time.sleep(2)
        
        print("\nStep 5: Daily report...")
        self.daily_report()
        
        print("\n" + "="*70)
        print("✅ Demo complete!")
        print("\n📊 View results:")
        print("   • Run 'streamlit run dashboard.py' to view dashboard")
        print("   • Check 'smartsubnet_alerts.log' for alert history")
        print("="*70)


if __name__ == "__main__":
    import sys
    
    system = SmartSubnetAI()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--continuous":
            system.run_continuous()
        elif sys.argv[1] == "--demo":
            system.run_demo()
        else:
            print("\nUsage:")
            print("  python main.py              Run demo mode (default)")
            print("  python main.py --demo       Run demonstration")
            print("  python main.py --continuous Run continuous monitoring")
    else:
        # Default: run demo
        system.run_demo()
