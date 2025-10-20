import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from database import DatabaseManager, SubnetAllocation, IPConflict, NetworkDevice, PredictionLog
from datetime import datetime, timedelta
from ml_predictor import SubnetDemandPredictor
from conflict_resolver import ConflictDetectionEngine
import ipaddress

# Page config
st.set_page_config(
    page_title="SmartSubnet AI",
    page_icon="🌐",
    layout="wide"
)

# Initialize database
@st.cache_resource
def get_db():
    return DatabaseManager('smartsubnet.db')

db = get_db()

# Header
st.title("🌐 SmartSubnet AI")
st.markdown("**Predictive IP Allocation for Scalable Data Centers**")
st.markdown("---")

# In sidebar
page = st.sidebar.radio("Go to", [
    "Dashboard",
    "Subnet Utilization",
    "ML Predictions",
    "Conflict Management",
    "Manual Allocation",
    "Cost Analysis"  # NEW
])

# DASHBOARD PAGE
if page == "Dashboard":
    st.header("📊 Network Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get latest statistics
    latest_allocations = db.session.query(SubnetAllocation).order_by(
        SubnetAllocation.timestamp.desc()
    ).limit(5).all()
    
    if latest_allocations:
        avg_util = sum([a.utilization_percent for a in latest_allocations]) / len(latest_allocations)
        total_ips = sum([a.total_ips for a in latest_allocations])
        allocated_ips = sum([a.allocated_ips for a in latest_allocations])
        
        col1.metric("Average Utilization", f"{avg_util:.1f}%")
        col2.metric("Total IP Addresses", f"{total_ips:,}")
        col3.metric("Allocated IPs", f"{allocated_ips:,}")
        col4.metric("Available IPs", f"{total_ips - allocated_ips:,}")
    
    # Conflicts summary
    st.subheader("🚨 Conflict Summary")
    col1, col2, col3 = st.columns(3)
    
    active_conflicts = db.session.query(IPConflict).filter_by(resolved=False).count()
    resolved_conflicts = db.session.query(IPConflict).filter_by(resolved=True).count()
    quarantined = db.session.query(NetworkDevice).filter_by(status='quarantined').count()
    
    col1.metric("Active Conflicts", active_conflicts, delta=None if active_conflicts == 0 else f"-{active_conflicts}")
    col2.metric("Resolved (24h)", resolved_conflicts)
    col3.metric("Quarantined Devices", quarantined)
    
    # Recent activity
    st.subheader("📈 Recent Subnet Activity")
    
    recent = db.session.query(SubnetAllocation).order_by(
        SubnetAllocation.timestamp.desc()
    ).limit(20).all()
    
    if recent:
        df = pd.DataFrame([{
            'Timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M'),
            'Subnet': r.subnet,
            'Department': r.department,
            'Utilization %': f"{r.utilization_percent:.1f}",
            'Allocated': r.allocated_ips,
            'Available': r.available_ips
        } for r in recent])
        
        st.dataframe(df, use_container_width=True)
    
    # Utilization trend chart
    st.subheader("📉 Utilization Trends (Last 7 Days)")
    
    week_ago = datetime.now() - timedelta(days=7)
    trend_data = db.session.query(SubnetAllocation).filter(
        SubnetAllocation.timestamp >= week_ago
    ).order_by(SubnetAllocation.timestamp).all()
    
    if trend_data:
        df_trend = pd.DataFrame([{
            'timestamp': r.timestamp,
            'subnet': r.subnet,
            'utilization': r.utilization_percent
        } for r in trend_data])
        
        fig = px.line(df_trend, x='timestamp', y='utilization', color='subnet',
                     title='Subnet Utilization Over Time',
                     labels={'utilization': 'Utilization %', 'timestamp': 'Date'})
        st.plotly_chart(fig, use_container_width=True)

# SUBNET UTILIZATION PAGE
elif page == "Subnet Utilization":
    st.header("📊 Subnet Utilization Analysis")
    
    # Get all subnets
    subnets = db.session.query(SubnetAllocation.subnet).distinct().all()
    subnet_list = [s[0] for s in subnets]
    
    selected_subnet = st.selectbox("Select Subnet", subnet_list)
    
    if selected_subnet:
        # Get data for selected subnet
        data = db.session.query(SubnetAllocation).filter_by(
            subnet=selected_subnet
        ).order_by(SubnetAllocation.timestamp.desc()).limit(100).all()
        
        if data:
            latest = data[0]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Utilization", f"{latest.utilization_percent:.1f}%")
            col2.metric("Allocated IPs", latest.allocated_ips)
            col3.metric("Available IPs", latest.available_ips)
            
            # Gauge chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = latest.utilization_percent,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Current Utilization"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgreen"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Historical chart
            df_hist = pd.DataFrame([{
                'timestamp': r.timestamp,
                'utilization': r.utilization_percent,
                'allocated': r.allocated_ips
            } for r in reversed(data)])
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_hist['timestamp'], y=df_hist['utilization'],
                                     mode='lines+markers', name='Utilization %'))
            fig2.update_layout(title='Historical Utilization',
                              xaxis_title='Date',
                              yaxis_title='Utilization %')
            
            st.plotly_chart(fig2, use_container_width=True)

# ML PREDICTIONS PAGE
elif page == "ML Predictions":
    st.header("🔮 Machine Learning Predictions")
    
    st.info("AI-powered forecasts help you stay ahead of capacity issues")
    
    col1, col2 = st.columns(2)
    
    with col1:
        forecast_days = st.slider("Forecast Period (days)", 1, 30, 7)
    
    with col2:
        if st.button("🚀 Generate Predictions", type="primary"):
            with st.spinner("Training models and generating forecasts..."):
                predictor = SubnetDemandPredictor(db)
                predictions = predictor.predict_all_subnets(days_ahead=forecast_days)
                st.success(f"✅ Generated {forecast_days}-day forecasts for {len(predictions)} subnets")
    
    # Show latest predictions
    st.subheader("📈 Latest Predictions")
    
    latest_preds = db.session.query(PredictionLog).order_by(
        PredictionLog.prediction_date.desc()
    ).limit(10).all()
    
    if latest_preds:
        df_preds = pd.DataFrame([{
            'Subnet': p.subnet,
            'Forecast Days': p.forecast_days,
            'Predicted Utilization %': f"{p.predicted_utilization:.1f}",
            'Confidence': f"{p.confidence_score:.2f}" if p.confidence_score else "N/A",
            'Generated': p.prediction_date.strftime('%Y-%m-%d %H:%M')
        } for p in latest_preds])
        
        st.dataframe(df_preds, use_container_width=True)
        
        # Visualization
        subnets_with_pred = list(set([p.subnet for p in latest_preds]))
        
        if subnets_with_pred:
            selected = st.selectbox("View Detailed Forecast", subnets_with_pred)
            
            subnet_preds = [p for p in latest_preds if p.subnet == selected]
            
            if subnet_preds:
                df_viz = pd.DataFrame([{
                    'date': p.prediction_date + timedelta(days=p.forecast_days),
                    'utilization': p.predicted_utilization
                } for p in subnet_preds])
                
                fig = px.line(df_viz, x='date', y='utilization',
                             title=f'Predicted Utilization for {selected}',
                             labels={'utilization': 'Utilization %', 'date': 'Date'})
                fig.add_hline(y=80, line_dash="dash", line_color="orange",
                             annotation_text="Warning Threshold")
                fig.add_hline(y=90, line_dash="dash", line_color="red",
                             annotation_text="Critical Threshold")
                
                st.plotly_chart(fig, use_container_width=True)

# CONFLICT MANAGEMENT PAGE
elif page == "Conflict Management":
    st.header("🛡️ Conflict Detection & Resolution")
    
    st.info("Automatic detection and resolution of IP conflicts")
    
    # Run scan button
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Run Network Scan", type="primary"):
            with st.spinner("Scanning network for conflicts..."):
                resolver = ConflictDetectionEngine(db)
                authorized = [
                    "192.168.1.0/24",
                    "192.168.2.0/24",
                    "10.0.1.0/24",
                    "10.0.2.0/24",
                    "172.16.1.0/24"
                ]
                conflicts = resolver.run_full_scan(authorized)
                st.success(f"✅ Scan complete! Found and resolved {conflicts} conflicts")
    
    with col2:
        report = ConflictDetectionEngine(db).get_conflict_report()
        st.metric("Resolution Rate", f"{report['resolution_rate']:.1f}%")
    
    # Active conflicts
    st.subheader("⚠️ Active Conflicts")
    
    active = db.session.query(IPConflict).filter_by(resolved=False).all()
    
    if active:
        df_active = pd.DataFrame([{
            'IP Address': c.ip_address,
            'Subnet': c.subnet,
            'Type': c.conflict_type,
            'Detected': c.detected_at.strftime('%Y-%m-%d %H:%M'),
            'ID': c.id
        } for c in active])
        
        st.dataframe(df_active, use_container_width=True)
        
        # Manual resolution
        st.subheader("Manual Resolution")
        conflict_id = st.number_input("Conflict ID to Resolve", min_value=1, step=1)
        resolution_method = st.text_input("Resolution Method", "Manual intervention")
        
        if st.button("✅ Mark as Resolved"):
            if db.resolve_conflict(conflict_id, resolution_method):
                st.success(f"Conflict {conflict_id} marked as resolved")
                st.rerun()
    else:
        st.success("✅ No active conflicts")
    
    # Resolved conflicts (last 24h)
    st.subheader("✅ Recently Resolved")
    
    day_ago = datetime.now() - timedelta(days=1)
    resolved = db.session.query(IPConflict).filter(
        IPConflict.resolved == True,
        IPConflict.resolved_at >= day_ago
    ).all()
    
    if resolved:
        df_resolved = pd.DataFrame([{
            'IP Address': c.ip_address,
            'Type': c.conflict_type,
            'Detected': c.detected_at.strftime('%Y-%m-%d %H:%M'),
            'Resolved': c.resolved_at.strftime('%Y-%m-%d %H:%M'),
            'Method': c.resolution_method
        } for c in resolved])
        
        st.dataframe(df_resolved, use_container_width=True)
    
    # Quarantined devices
    st.subheader("🚨 Quarantined Devices")
    
    quarantined = db.session.query(NetworkDevice).filter_by(status='quarantined').all()
    
    if quarantined:
        df_quar = pd.DataFrame([{
            'Device': d.device_name,
            'Current IP': d.ip_address,
            'Type': d.device_type,
            'Last Seen': d.last_seen.strftime('%Y-%m-%d %H:%M')
        } for d in quarantined])
        
        st.dataframe(df_quar, use_container_width=True)
    else:
        st.info("No devices in quarantine")

# MANUAL ALLOCATION PAGE
elif page == "Manual Allocation":
    st.header("⚙️ Manual Subnet Allocation")
    
    st.info("Review AI recommendations and approve/modify allocations")
    
    # Input for new subnet requirements
    st.subheader("📝 New Allocation Request")
    
    col1, col2 = st.columns(2)
    
    with col1:
        network = st.text_input("Base Network (CIDR)", "192.168.0.0/16")
        department = st.text_input("Department", "Engineering")
    
    with col2:
        hosts_needed = st.number_input("Hosts Required", min_value=1, max_value=10000, value=100)
    
    if st.button("🧮 Calculate Optimal Subnet"):
        try:
            from subnet_calculator import SubnetCalculator
            
            calc = SubnetCalculator(network)
            allocation = calc.vlsm_allocation([hosts_needed])
            
            if allocation:
                result = allocation[0]
                
                st.success(f"✅ Recommended subnet: {result['subnet']}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Allocated Hosts", result['usable_hosts'])
                col2.metric("First Usable IP", result['first_usable'])
                col3.metric("Last Usable IP", result['last_usable'])
                
                if st.button("✅ Approve and Apply", type="primary"):
                    # Add to database
                    db.add_subnet_allocation(
                        result['subnet'],
                        result['usable_hosts'],
                        0,  # Initially 0 allocated
                        department
                    )
                    st.success("Subnet allocation approved and added to database!")
        except Exception as e:
            st.error(f"Error: {e}")
    
    # Show pending approvals (simulated)
    st.subheader("📋 Pending Approvals")
    
    st.info("No pending allocation requests at this time")
    
    # COST ANALYSIS PAGE
elif page == "Cost Analysis":
    st.header("💰 Cost Analysis & Savings")
    
    from cost_analyzer import CostAnalyzer
    
    analyzer = CostAnalyzer(db)
    
    if st.button("🔄 Refresh Analysis", type="primary"):
        report = analyzer.generate_cost_report()
        st.success("Analysis updated!")
    
    # Current waste
    st.subheader("📊 Current IP Waste")
    
    waste = analyzer.calculate_ip_waste()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total IPs", f"{waste['total_allocated']:,}")
    col2.metric("Used IPs", f"{waste['total_used']:,}")
    col3.metric("Wasted IPs", f"{waste['total_wasted']:,}")
    col4.metric("Waste %", f"{waste['waste_percentage']:.1f}%")
    
    # Waste gauge
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = waste['waste_percentage'],
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "IP Waste Percentage"},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "red"},
            'steps': [
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 40], 'color': "yellow"},
                {'range': [40, 100], 'color': "lightcoral"}
            ]
        }
    ))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Cost impact
    st.subheader("💵 Financial Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Monthly Waste Cost", f"${waste['monthly_waste_cost']:.2f}")
        st.metric("Annual Waste Cost", f"${waste['annual_waste_cost']:.2f}")
    
    # Savings potential
    st.subheader("💡 Optimization Potential")
    
    savings = analyzer.calculate_optimization_savings()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Recoverable IPs", f"{savings['recoverable_ips']:.0f}")
    col2.metric("Annual IP Savings", f"${savings['annual_ip_savings']:.2f}")
    col3.metric("Total Annual Savings", f"${savings['total_annual_savings']:.2f}")
    
    # ROI
    if savings['total_annual_savings'] > 0:
        st.success(f"🎯 ROI: Break even in {analyzer._calculate_roi():.1f} months")
    
    # Recommendations
    st.subheader("📋 Recommendations")
    
    st.info("""
    **To reduce IP waste:**
    1. ✅ Implement automated IP reclamation
    2. ✅ Right-size subnets based on actual usage
    3. ✅ Regularly audit and clean up unused allocations
    4. ✅ Use ML predictions to prevent over-provisioning
    """)
\
# Footer
st.markdown("---")
st.markdown("**SmartSubnet AI** v1.0 | Predictive IP Allocation for Modern Data Centers")
