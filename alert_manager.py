from datetime import datetime
from database import DatabaseManager, SubnetAllocation, IPConflict
import ipaddress

class AlertManager:
    """
    Manage alerts by logging to console (perfect for testing/development)
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Alert thresholds
        self.thresholds = {
            'warning': 80,    # 80% utilization
            'critical': 90,   # 90% utilization
            'forecast_days': 7  # Alert if critical within 7 days
        }
        
        print("📧 Alert Manager initialized (Console Mode)")
    
    def send_email(self, subject, body, priority='normal'):
        """Print alert to console instead of sending email"""
        priority_icon = "🚨" if priority == 'high' else "📧"
        
        print("\n" + "="*70)
        print(f"{priority_icon} ALERT [{priority.upper()}]: {subject}")
        print("="*70)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*70)
        print(body)
        print("="*70 + "\n")
        
        # Log to file as well
        self._log_to_file(subject, body, priority)
        
        print(f"✅ Alert logged: {subject}")
        return True
    
    def _log_to_file(self, subject, body, priority):
        """Save alerts to a log file"""
        try:
            with open('smartsubnet_alerts.log', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{priority.upper()}]\n")
                f.write(f"Subject: {subject}\n")
                f.write(f"{'-'*70}\n")
                f.write(f"{body}\n")
                f.write(f"{'='*70}\n")
        except Exception as e:
            print(f"⚠️  Could not write to log file: {e}")
    
    def check_utilization_alerts(self):
        """Check for high utilization and send alerts"""
        print("\n🔍 Checking for utilization alerts...")
        
        # Get latest allocations
        recent = self.db.session.query(SubnetAllocation).order_by(
            SubnetAllocation.timestamp.desc()
        ).limit(10).all()
        
        alerts = []
        
        for alloc in recent:
            if alloc.utilization_percent >= self.thresholds['critical']:
                alerts.append({
                    'level': 'CRITICAL',
                    'subnet': alloc.subnet,
                    'utilization': alloc.utilization_percent,
                    'available': alloc.available_ips
                })
            elif alloc.utilization_percent >= self.thresholds['warning']:
                alerts.append({
                    'level': 'WARNING',
                    'subnet': alloc.subnet,
                    'utilization': alloc.utilization_percent,
                    'available': alloc.available_ips
                })
        
        if alerts:
            self._send_utilization_alert(alerts)
        else:
            print("   ✅ No utilization alerts")
        
        return alerts
    
    def check_conflict_alerts(self):
        """Check for unresolved conflicts"""
        print("\n🔍 Checking for conflict alerts...")
        
        active_conflicts = self.db.session.query(IPConflict).filter_by(
            resolved=False
        ).all()
        
        if active_conflicts:
            self._send_conflict_alert(active_conflicts)
            print(f"   ⚠️  {len(active_conflicts)} active conflicts")
        else:
            print("   ✅ No active conflicts")
        
        return active_conflicts
    
    def check_prediction_alerts(self, predictions):
        """Check if predictions indicate future problems"""
        print("\n🔍 Checking prediction-based alerts...")
        
        alerts = []
        
        for subnet, pred_df in predictions.items():
            max_predicted = pred_df['predicted_utilization'].max()
            
            if max_predicted >= self.thresholds['critical']:
                days_to_critical = None
                for idx, row in pred_df.iterrows():
                    if row['predicted_utilization'] >= self.thresholds['critical']:
                        days_to_critical = (row['date'] - datetime.now()).days
                        break
                
                alerts.append({
                    'subnet': subnet,
                    'max_predicted': max_predicted,
                    'days_to_critical': days_to_critical
                })
        
        if alerts:
            self._send_prediction_alert(alerts)
        else:
            print("   ✅ No prediction alerts")
        
        return alerts
    
    def _send_utilization_alert(self, alerts):
        """Send utilization alert"""
        body = "High Utilization Detected:\n\n"
        
        for alert in alerts:
            body += f"[{alert['level']}] Subnet: {alert['subnet']}\n"
            body += f"  Utilization: {alert['utilization']:.1f}%\n"
            body += f"  Available IPs: {alert['available']}\n\n"
        
        body += "Recommended Actions:\n"
        body += "1. Review and reclaim unused IP addresses\n"
        body += "2. Consider subnet expansion or reallocation\n"
        body += "3. Check for IP conflicts or unauthorized devices\n"
        
        priority = 'high' if any(a['level'] == 'CRITICAL' for a in alerts) else 'normal'
        self.send_email("High Utilization Alert", body, priority)
    
    def _send_conflict_alert(self, conflicts):
        """Send conflict alert"""
        body = f"Active IP Conflicts Detected: {len(conflicts)}\n\n"
        
        for conflict in conflicts[:10]:  # Limit to first 10
            body += f"IP: {conflict.ip_address}\n"
            body += f"  Subnet: {conflict.subnet}\n"
            body += f"  Type: {conflict.conflict_type}\n"
            body += f"  Detected: {conflict.detected_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        if len(conflicts) > 10:
            body += f"... and {len(conflicts) - 10} more conflicts\n\n"
        
        body += "Action Required: Review conflicts in dashboard\n"
        
        self.send_email("IP Conflict Alert", body, priority='high')
    
    def _send_prediction_alert(self, alerts):
        """Send prediction-based alert"""
        body = "Capacity Warning - Future Utilization Concerns:\n\n"
        
        for alert in alerts:
            body += f"Subnet: {alert['subnet']}\n"
            body += f"  Predicted Peak: {alert['max_predicted']:.1f}%\n"
            body += f"  Days to Critical: {alert['days_to_critical']}\n\n"
        
        body += "Recommended Actions:\n"
        body += "1. Plan for subnet expansion\n"
        body += "2. Review allocation policies\n"
        body += "3. Consider implementing address reclamation\n"
        
        self.send_email("Capacity Forecast Alert", body, priority='normal')
    
    def generate_daily_report(self):
        """Generate and display daily summary report"""
        print("\n📊 Generating daily report...")
        
        # Utilization stats
        recent = self.db.session.query(SubnetAllocation).order_by(
            SubnetAllocation.timestamp.desc()
        ).limit(10).all()
        
        avg_util = sum([r.utilization_percent for r in recent]) / len(recent) if recent else 0
        
        # Conflict stats
        active_conflicts = self.db.session.query(IPConflict).filter_by(resolved=False).count()
        resolved_today = self.db.session.query(IPConflict).filter_by(resolved=True).count()
        
        body = f"""
Daily Network Report - {datetime.now().strftime('%Y-%m-%d')}

UTILIZATION SUMMARY:
  Average Utilization: {avg_util:.1f}%
  Subnets Monitored: {len(set([r.subnet for r in recent]))}

CONFLICT SUMMARY:
  Active Conflicts: {active_conflicts}
  Resolved Today: {resolved_today}

TOP UTILIZED SUBNETS:
"""
        
        sorted_recent = sorted(recent, key=lambda x: x.utilization_percent, reverse=True)
        for r in sorted_recent[:5]:
            body += f"  {r.subnet}: {r.utilization_percent:.1f}%\n"
        
        body += "\n---\nFor detailed analysis, visit the SmartSubnet AI dashboard.\n"
        
        self.send_email("Daily Network Report", body)


# Test alert manager
if __name__ == "__main__":
    print("="*70)
    print("    ALERT MANAGER TEST (CONSOLE MODE)")
    print("="*70)
    
    from database import DatabaseManager
    
    db = DatabaseManager('smartsubnet.db')
    
    # Initialize with console logger
    alert_mgr = AlertManager(db)
    
    # Test checks
    alert_mgr.check_utilization_alerts()
    alert_mgr.check_conflict_alerts()
    
    # Test direct alert
    print("\n📧 Testing direct alert...")
    alert_mgr.send_email("Test Alert", "This is a test from SmartSubnet AI\n\nSystem Status: OK")
    
    # Generate daily report
    alert_mgr.generate_daily_report()
    
    print("\n✅ Alert manager ready!")
    print("📄 Check 'smartsubnet_alerts.log' for saved alerts")
    
    db.close()
