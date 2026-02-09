import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta

class DataIngestor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir


    def _optimize_memory(self, df):
        """Downcasts types to reduce memory usage."""
        if df is None: return None
        
        # Downcast Numbers
        for col in df.select_dtypes(include=['float']):
            df[col] = pd.to_numeric(df[col], downcast='float')
        for col in df.select_dtypes(include=['int']):
            df[col] = pd.to_numeric(df[col], downcast='integer')
            
        # Convert low-cardinality objects to category
        for col in df.select_dtypes(include=['object']):
            if df[col].nunique() / len(df) < 0.5: # If < 50% unique
                df[col] = df[col].astype('category')
                
        return df

    def _read_enhanced(self, file, filename):
        """Enhanced loader that handles multiple formats and encoding logic."""
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            return pd.read_excel(file, engine='openpyxl')
            
        elif filename.endswith('.parquet'):
            return pd.read_parquet(file, engine='pyarrow')
            
        elif filename.endswith('.json'):
            try:
                return pd.read_json(file, orient='records')
            except:
                file.seek(0)
                return pd.read_json(file)
                
        else: # Default to CSV
            try:
                return pd.read_csv(file, low_memory=False, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                return pd.read_csv(file, low_memory=False, encoding='latin1')
            except Exception:
                file.seek(0)
                return pd.read_csv(file, low_memory=False, sep=';', encoding='latin1') # Euro CSV fallback

    def load_data(self, uploaded_files=None):
        """Loads data from CSV files in the data directory OR from uploaded file buffers."""
        required_keys = ["orders", "payments", "reviews"]
        data = {}

        # 1. Handle Uploaded Files (Priority)
        if uploaded_files:
            print("Loading from uploaded files...")
            try:
                for key in required_keys:
                    if key in uploaded_files and uploaded_files[key] is not None:
                        file = uploaded_files[key]
                        filename = file.name.lower()
                        print(f"Loading uploaded {key}: {filename}")
                        
                        # Load Data
                        df = self._read_enhanced(file, filename)
                        
                        # Normalize & Optimize
                        if df is not None:
                            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                            data[key] = self._optimize_memory(df)
                            
                        print(f"Loaded uploaded {key}: {len(data[key])} rows")
                
                if len(data) == 3:
                    return data
                else:
                    print("Incomplete uploaded files. Falling back to local data...")
            except Exception as e:
                print(f"Error reading uploaded files: {e}")


        # 2. Fallback to Local Files (data/ folder)
        required_files = {
            "orders": "olist_orders_dataset.csv",
            "payments": "olist_order_payments_dataset.csv",
            "reviews": "olist_order_reviews_dataset.csv"
        }
        
        missing_files = []

        if not os.path.exists(self.data_dir):
            print(f"Data directory '{self.data_dir}' not found.")
            return None

        for key, filename in required_files.items():
            path = os.path.join(self.data_dir, filename)
            if os.path.exists(path):
                try:
                    data[key] = pd.read_csv(path)
                    print(f"Loaded {key}: {len(data[key])} rows")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    missing_files.append(filename)
            else:
                missing_files.append(filename)
        
        if missing_files:
            print(f"Missing files: {missing_files}")
            return None
            
        return data

class DataCleaner:
    def clean_orders(self, df):
        # Convert dates
        date_cols = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Deduplicate
        df = df.drop_duplicates("order_id")
        return df

    def clean_reviews(self, df):
        # Handle missing text
        if 'review_comment_message' not in df.columns:
            df['review_comment_message'] = ""
        else:
            df['review_comment_message'] = df['review_comment_message'].fillna("")
            
        if 'review_comment_title' not in df.columns:
            df['review_comment_title'] = ""
        else:
            df['review_comment_title'] = df['review_comment_title'].fillna("")
        return df

    def merge_datasets(self, orders, payments, reviews):
        """Merges orders, payments, and reviews into a single DataFrame."""
        if orders is None or payments is None or reviews is None:
            return pd.DataFrame()
            
        # Merge orders and payments
        # Use inner join for payments to ensure we have value, left join for reviews
        df = pd.merge(orders, payments, on="order_id", how="left")
        
        # Merge with reviews
        df = pd.merge(df, reviews, on="order_id", how="left")
        
        return df

    def normalize_columns(self, df):
        """Standardizes column names to snake_case and lowercase."""
        if df is None: return None
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df

class SchemaValidator:
    """Ensures that the ingested data has the minimum required structure."""
    
    REQUIRED_COLUMNS = {
        "orders": ["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
        "payments": ["order_id", "payment_value"],
        "reviews": ["order_id", "review_comment_message"] # Minimal for AI analysis
    }

    def validate(self, data):
        """
        Checks missing columns and prints warnings.
        Returns validated (and potentially normalized) data keys.
        """
        issues = []
        for key, cols in self.REQUIRED_COLUMNS.items():
            if key not in data or data[key] is None:
                issues.append(f"Missing dataset: {key}")
                continue
                
            df = data[key]
            missing = [c for c in cols if c not in df.columns]
            if missing:
                issues.append(f"Dataset '{key}' missing columns: {missing}")
        
        if issues:
            print("--- Schema Validation Issues ---")
            for issue in issues:
                print(f"ALERTA: {issue}")
            print("--------------------------------")
        
        return len(issues) == 0

class MetricsEngine:
    def calculate_ltv(self, full_df):
        """Calculates LTV per customer."""
        if 'payment_value' not in full_df or 'customer_id' not in full_df:
            return pd.DataFrame()
        
        ltv = full_df.groupby('customer_id')['payment_value'].sum().reset_index()
        ltv.columns = ['customer_id', 'ltv']
        return ltv

    def calculate_churn_risk(self, orders_df):
        """
        Identify customers who haven't bought in a long time (churn risk).
        For Olist (non-subscription), this is just 'dormant users'.
        """
        if 'order_purchase_timestamp' not in orders_df:
            return pd.DataFrame()

        max_date = orders_df['order_purchase_timestamp'].max()
        
        # Latest purchase per customer
        recency = orders_df.groupby('customer_id')['order_purchase_timestamp'].max().reset_index()
        recency['days_since_last_order'] = (max_date - recency['order_purchase_timestamp']).dt.days
        
        # Retail Logic: Active Customers (Last 30 days)
        # Instead of generic Churn, we track who is "Alive" in the ecosystem
        recency['is_active_30d'] = np.where(recency['days_since_last_order'] <= 30, True, False)
        
        return recency

def generate_mock_data(data_dir="data"):
    """Generates sample CSVs for testing logic."""
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    print("Generating mock data...")
    
    # Orders
    orders = pd.DataFrame({
        "order_id": [f"ord_{i}" for i in range(10)],
        "customer_id": [f"cust_{i%4}" for i in range(10)], # 4 unique customers
        "order_status": ["delivered"] * 10,
        "order_purchase_timestamp": [datetime.now() - timedelta(days=i*30) for i in range(10)]
    })
    orders.to_csv(os.path.join(data_dir, "olist_orders_dataset.csv"), index=False)
    
    # Payments
    payments = pd.DataFrame({
        "order_id": [f"ord_{i}" for i in range(10)],
        "payment_value": [100.0 + i*10 for i in range(10)]
    })
    payments.to_csv(os.path.join(data_dir, "olist_order_payments_dataset.csv"), index=False)
    
    # Reviews
    reviews = pd.DataFrame({
        "order_id": [f"ord_{i}" for i in range(10)],
        "review_score": [5, 1, 5, 4, 1, 3, 5, 5, 2, 5],
        "review_comment_title": ["", "Ruim", "", "", "Não", "Medio", "Uau", "Bom", "Ruim", "Perf"],
        "review_comment_message": ["Ótimo!", "Entrega terrível, atrasou", "Amei", "Ok", "Nunca mais compro", "Médio", "Soberbo", "Bom", "Produto ruim", "Perfeito"]
    })
    reviews.to_csv(os.path.join(data_dir, "olist_order_reviews_dataset.csv"), index=False)
    print("Mock data generated.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run with mock data test")
    parser.add_argument("--generate-mock", action="store_true", help="Generate mock data")
    args = parser.parse_args()

    if args.generate_mock:
        generate_mock_data()
    
    if args.test:
        print("\n--- Running Pipeline Test ---")
        ingestor = DataIngestor()
        # Ensure data exists or mock it
        if ingestor.load_data() is None:
            generate_mock_data()
            
        raw_data = ingestor.load_data()
        if raw_data:
            cleaner = DataCleaner()
            orders = cleaner.clean_orders(raw_data['orders'])
            reviews = cleaner.clean_reviews(raw_data['reviews'])
            full_data = cleaner.merge_datasets(orders, raw_data['payments'], reviews)
            
            print(f"Merged Data Shape: {full_data.shape}")
            
            metrics = MetricsEngine()
            ltv = metrics.calculate_ltv(full_data)
            churn = metrics.calculate_churn_risk(orders)
            
            print("\nHead of LTV:")
            print(ltv.head())
            print("\nHead of Churn Risk:")
            print(churn.head())
            print("\nPipeline Test Complete.")
