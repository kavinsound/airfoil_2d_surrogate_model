import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pandas as pd
import copy
import joblib
import matplotlib.pyplot as plt
from pytorch_nn import AeroSurrogateMLP


df = pd.read_csv("sim_data.csv")

columns = ["CD", "CL"]

y_raw = df[columns].copy()
x_raw = df[df.columns.difference(columns)].copy()

weights = joblib.load("model_weights.pth")

model = AeroSurrogateMLP()

model.load_state_dict(weights['model_state_dict'])

scaler_x = weights['scaler_x']
scaler_y = weights['scaler_y']

model.eval()

x_scaled = scaler_x.transform(x_raw)

# Convert the numpy array to a PyTorch float tensor
x_tensor = torch.tensor(x_scaled, dtype=torch.float32)

# --- 2. Perform the Data Passthrough (Inference) ---
# Use torch.no_grad() to freeze gradient tracking (saves memory and speed)
with torch.no_grad():
    scaled_predictions_tensor = model(x_tensor)
    
    # Convert back to a NumPy array so scikit-learn/pandas can read it
    scaled_predictions = scaled_predictions_tensor.numpy()

# --- 3. Inverse-Transform Back to Physical Aerodynamic Units ---
# This converts the model output back to the real 0.2 - 1.0 physical scale
real_predictions = scaler_y.inverse_transform(scaled_predictions)
real_actuals = y_raw.values  # True CD and CL values from your CSV

from sklearn.metrics import r2_score

# 1. Calculate R2 Score (Standard ML Metric)
r2_cd = r2_score(real_actuals[:, 0], real_predictions[:, 0])
r2_cl = r2_score(real_actuals[:, 1], real_predictions[:, 1])

# 2. Calculate Normalized RMSE (Using Range to avoid dividing by zero)
rmse_per_col = np.sqrt(np.mean((real_actuals - real_predictions)**2, axis=0))
range_per_col = np.max(real_actuals, axis=0) - np.min(real_actuals, axis=0)
nrmse_per_col = (rmse_per_col / range_per_col) * 100

print("--- REVISED GLOBAL METRICS ---")
print(f"CD (Drag Coefficient):")
print(f"  R² Score:                 {r2_cd:.4f} (Ideally close to 1.0)")
print(f"  Normalized Error (NRMSE): {nrmse_per_col[0]:.2f}%")
print(f"  Resume Accuracy Rating:   {100 - nrmse_per_col[0]:.2f}%")

print(f"\nCL (Lift Coefficient):")
print(f"  R² Score:                 {r2_cl:.4f}")
print(f"  Normalized Error (NRMSE): {nrmse_per_col[1]:.2f}%")
print(f"  Resume Accuracy Rating:   {100 - nrmse_per_col[1]:.2f}%")