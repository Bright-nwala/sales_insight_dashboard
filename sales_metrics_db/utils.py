import pandas as pd
import os

def load_data(filename="cleaned_data.csv"):
    # Build path relative to this file (utils.py)
    base_dir = os.path.dirname(__file__)  # folder where utils.py is located
    data_path = os.path.join(base_dir, "data", filename)
    return pd.read_csv(data_path)

