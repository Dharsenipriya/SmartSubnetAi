import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import DatabaseManager, SubnetAllocation, PredictionLog
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class SubnetDemandPredictor:
    """
    Machine Learning model to predict subnet utilization
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.models = {}  # Store model for each subnet
        print("🤖 ML Predictor initialized")
    
    def load_training_data(self, subnet, days_back=30):
        """Load historical data for a subnet"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        records = self.db.session.query(SubnetAllocation).filter(
            SubnetAllocation.subnet == subnet,
            SubnetAllocation.timestamp >= cutoff_date
        ).order_by(SubnetAllocation.timestamp).all()
        
        if not records:
            print(f"⚠️  No historical data found for {subnet}")
            return None
        
        # Convert to DataFrame
        data = []
        for record in records:
            data.append({
                'timestamp': record.timestamp,
                'utilization': record.utilization_percent,
                'allocated': record.allocated_ips,
                'total': record.total_ips
            })
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df)} records for {subnet}")
        return df
    
    def prepare_features(self, df):
        """Create features from timestamp"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        
        # Numerical time feature (days since start)
        df['days_since_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 86400
        
        return df
    
    def train_model(self, subnet):
        """Train prediction model for a subnet"""
        print(f"\n🎓 Training model for {subnet}...")
        
        df = self.load_training_data(subnet)
        if df is None or len(df) < 10:
            print(f"❌ Insufficient data for training (need at least 10 records)")
            return False
        
        df = self.prepare_features(df)
        
        # Features: days_since_start, hour, day_of_week
        X = df[['days_since_start', 'hour', 'day_of_week']].values
        y = df['utilization'].values
        
        # Train simple linear regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate accuracy on training data
        predictions = model.predict(X)
        mae = mean_absolute_error(y, predictions)
        r2 = r2_score(y, predictions)
        
        print(f"   MAE: {mae:.2f}% | R² Score: {r2:.3f}")
        
        # Store model
        self.models[subnet] = {
            'model': model,
            'start_date': df['timestamp'].min(),
            'mae': mae,
            'r2': r2
        }
        
        print(f"✅ Model trained successfully")
        return True
    
    def predict_utilization(self, subnet, days_ahead=7):
        """Predict utilization for future days"""
        if subnet not in self.models:
            print(f"⚠️  No model found for {subnet}. Training now...")
            if not self.train_model(subnet):
                return None
        
        model_info = self.models[subnet]
        model = model_info['model']
        start_date = model_info['start_date']
        
        # Generate future dates
        future_dates = []
        predictions = []
        
        for day in range(1, days_ahead + 1):
            future_date = datetime.now() + timedelta(days=day)
            
            # Calculate days since start
            days_since = (future_date - start_date).total_seconds() / 86400
            
            # Features
            features = np.array([[
                days_since,
                future_date.hour,
                future_date.weekday()
            ]])
            
            pred = model.predict(features)[0]
            
            # Ensure prediction is within reasonable bounds
            pred = max(0, min(100, pred))
            
            future_dates.append(future_date)
            predictions.append(pred)
        
        # Create results dataframe
        results = pd.DataFrame({
            'date': future_dates,
            'predicted_utilization': predictions
        })
        
        # Save predictions to database
        for _, row in results.iterrows():
            pred_log = PredictionLog(
                subnet=subnet,
                forecast_days=days_ahead,
                predicted_utilization=row['predicted_utilization'],
                confidence_score=model_info['r2']
            )
            self.db.session.add(pred_log)
        
        self.db.session.commit()
        
        return results
    
    def predict_all_subnets(self, days_ahead=7):
        """Generate predictions for all known subnets"""
        # Get unique subnets from database
        subnets = self.db.session.query(SubnetAllocation.subnet).distinct().all()
        subnets = [s[0] for s in subnets]
        
        print(f"\n🔮 Generating {days_ahead}-day forecasts for {len(subnets)} subnets")
        print("="*60)
        
        all_predictions = {}
        
        for subnet in subnets:
            predictions = self.predict_utilization(subnet, days_ahead)
            if predictions is not None:
                all_predictions[subnet] = predictions
                
                avg_util = predictions['predicted_utilization'].mean()
                max_util = predictions['predicted_utilization'].max()
                
                print(f"\n📊 {subnet}")
                print(f"   Average predicted: {avg_util:.1f}%")
                print(f"   Peak predicted: {max_util:.1f}%")
                
                if max_util > 90:
                    print(f"   ⚠️  WARNING: Approaching capacity!")
                elif max_util > 80:
                    print(f"   ⚡ Alert: High utilization expected")
        
        return all_predictions
    
    def evaluate_past_predictions(self):
        """Compare past predictions with actual utilization"""
        print("\n📈 Evaluating prediction accuracy...")
        
        # Get predictions made in the past
        past_predictions = self.db.session.query(PredictionLog).filter(
            PredictionLog.prediction_date < datetime.now() - timedelta(days=7)
        ).all()
        
        if not past_predictions:
            print("No past predictions to evaluate yet")
            return
        
        accuracies = []
        
        for pred in past_predictions[:10]:  # Sample first 10
            # Find actual utilization near the prediction target date
            target_date = pred.prediction_date + timedelta(days=pred.forecast_days)
            
            actual = self.db.session.query(SubnetAllocation).filter(
                SubnetAllocation.subnet == pred.subnet,
                SubnetAllocation.timestamp >= target_date - timedelta(hours=12),
                SubnetAllocation.timestamp <= target_date + timedelta(hours=12)
            ).order_by(SubnetAllocation.timestamp.desc()).first()
            
            if actual:
                error = abs(pred.predicted_utilization - actual.utilization_percent)
                accuracies.append(100 - error)
                
                print(f"   {pred.subnet}: Predicted {pred.predicted_utilization:.1f}% | Actual {actual.utilization_percent:.1f}% | Error: {error:.1f}%")
        
        if accuracies:
            avg_accuracy = np.mean(accuracies)
            print(f"\n✅ Average prediction accuracy: {avg_accuracy:.1f}%")


# Test ML predictor
if __name__ == "__main__":
    print("="*60)
    print("    ML PREDICTION ENGINE TEST")
    print("="*60)
    
    # Initialize
    db = DatabaseManager('smartsubnet.db')
    predictor = SubnetDemandPredictor(db)
    
    # Train models and generate predictions
    predictions = predictor.predict_all_subnets(days_ahead=7)
    
    # Show detailed predictions for one subnet
    if predictions:
        sample_subnet = list(predictions.keys())[0]
        print(f"\n📋 Detailed 7-day forecast for {sample_subnet}:")
        print("="*60)
        df = predictions[sample_subnet]
        for _, row in df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d %H:%M')
            util = row['predicted_utilization']
            bar = "█" * int(util / 5)
            print(f"   {date_str} | {util:5.1f}% | {bar}")
    
    db.close()
