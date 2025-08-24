import os
import pandas as pd

def load_data(filename="cleaned_data.csv"):
    # Get absolute path to the folder where utils.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Point to /data/cleaned_data.csv relative to utils.py
    file_path = os.path.join(base_dir, "data", filename)
    return pd.read_csv(file_path)




