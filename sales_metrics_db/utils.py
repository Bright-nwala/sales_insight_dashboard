import pandas as pd
import os

def load_data(filename="cleaned_data.csv"):
    base_dir = os.path.dirname(__file__)  # path to sales_metrics_db/
    data_path = os.path.join(base_dir, "data", filename)  
    return pd.read_csv(data_path)



