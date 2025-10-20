from database import DatabaseManager, SubnetAllocation
from datetime import datetime, timedelta
import pandas as pd

class CostAnalyzer:
    """
    Calculate IP waste and cost savings
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        
        # Cost assumptions (customize for your org)
        self.costs = {
            'ip_cost_per_month': 0.50,  # Cost per allocated IP per month
            'subnet_admin_hours': 2,     # Hours per subnet per month
            'hourly_rate': 50            # Admin hourly rate
        }
        
        print("💰 Cost Analyzer initialized")
    
    def calculate_ip_waste(self):
        """Calculate wasted IPs across all subnets"""
        print("\n📊 Calculating IP waste...")
        
        recent = self.db.session.query(SubnetAllocation).order_by(
            SubnetAllocation.timestamp.desc()
        ).limit(20).all()
        
        total_allocated = sum([r.total_ips for r in recent])
        total_used = sum([r.allocated_ips for r in recent])
        total_wasted = total_allocated - total_used
        
        waste_percentage = (total_wasted / total_allocated * 100) if total_allocated > 0 else 0
        
        # Calculate cost of waste
        monthly_waste_cost = total_wasted * self.costs['ip_cost_per_month']
        annual_waste_cost = monthly_waste_cost * 12
        
        result = {
            'total_allocated': total_allocated,
            'total_used': total_used,
            'total_wasted': total_wasted,
            'waste_percentage': waste_percentage,
            'monthly_waste_cost': monthly_waste_cost,
            'annual_waste_cost': annual_waste_cost
        }
        
        print(f"  Total IPs: {total_allocated}")
        print(f"  Used: {total_used}")
        print(f"  Wasted: {total_wasted} ({waste_percentage:.1f}%)")
        print(f"  Monthly Cost: ${monthly_waste_cost:.2f}")
        print(f"  Annual Cost: ${annual_waste_cost:.2f}")
        
        return result
    
    def calculate_optimization_savings(self):
        """Calculate potential savings from optimization"""
        waste = self.calculate_ip_waste()
        
        # Assume 50% of waste can be recovered through optimization
        recoverable = waste['total_wasted'] * 0.5
        monthly_savings = recoverable * self.costs['ip_cost_per_month']
        annual_savings = monthly_savings * 12
        
        # Add admin time savings
        current_subnets = len(set([r.subnet for r in self.db.session.query(
            SubnetAllocation.subnet
        ).distinct().all()]))
        
        optimized_subnets = int(current_subnets * 0.8)  # 20% reduction
        subnet_savings = (current_subnets - optimized_subnets) * \
                        self.costs['subnet_admin_hours'] * \
                        self.costs['hourly_rate']
        
        result = {
            'recoverable_ips': recoverable,
            'monthly_ip_savings': monthly_savings,
            'annual_ip_savings': annual_savings,
            'monthly_admin_savings': subnet_savings,
            'total_annual_savings': annual_savings + (subnet_savings * 12)
        }
        
        print("\n💡 Optimization Potential:")
        print(f"  Recoverable IPs: {recoverable:.0f}")
        print(f"  Annual IP Savings: ${annual_savings:.2f}")
        print(f"  Annual Admin Savings: ${subnet_savings * 12:.2f}")
        print(f"  Total Annual Savings: ${result['total_annual_savings']:.2f}")
        
        return result
    
    def generate_cost_report(self):
        """Generate comprehensive cost report"""
        waste = self.calculate_ip_waste()
        savings = self.calculate_optimization_savings()
        
        report = {
            'current_state': waste,
            'optimization_potential': savings,
            'roi_months': self._calculate_roi()
        }
        
        return report
    
    def _calculate_roi(self):
        """Calculate ROI period for SmartSubnet AI"""
        # Assuming implementation cost
        implementation_cost = 5000  # One-time cost
        
        savings = self.calculate_optimization_savings()
        monthly_savings = savings['monthly_ip_savings'] + savings['monthly_admin_savings']
        
        if monthly_savings > 0:
            roi_months = implementation_cost / monthly_savings
            print(f"\n📈 ROI: {roi_months:.1f} months to break even")
            return roi_months
        
        return None


# Test cost analyzer
if __name__ == "__main__":
    print("="*60)
    print("    COST ANALYZER TEST")
    print("="*60)
    
    from database import DatabaseManager
    
    db = DatabaseManager('smartsubnet.db')
    analyzer = CostAnalyzer(db)
    
    report = analyzer.generate_cost_report()
    
    db.close()
