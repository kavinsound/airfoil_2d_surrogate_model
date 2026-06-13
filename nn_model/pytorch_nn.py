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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def createSet(df):
    columns = ["CD", "CL"]

    y_raw = df[columns].copy()
    x_raw = df[df.columns.difference(columns)].copy()

    x_train_raw, x_test_raw, y_train_raw, y_test_raw = train_test_split(x_raw, y_raw, test_size=0.2, random_state=67)

    scaler_x, scaler_y = StandardScaler(), StandardScaler()

    x_train_scaled = scaler_x.fit_transform(x_train_raw)
    y_train_scaled = scaler_y.fit_transform(y_train_raw)

    x_test_scaled = scaler_x.transform(x_test_raw)
    y_test_scaled = scaler_y.transform(y_test_raw)

    x_train_tensor = torch.tensor(x_train_scaled, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train_scaled, dtype=torch.float32)
    x_test_tensor = torch.tensor(x_test_scaled, dtype=torch.float32)
    y_test_tensor = torch.tensor(y_test_scaled, dtype=torch.float32)

    train_set = TensorDataset(x_train_tensor, y_train_tensor)
    test_set = TensorDataset(x_test_tensor, y_test_tensor)

    return train_set, test_set, scaler_x, scaler_y


class AeroSurrogateMLP(nn.Module):
    def __init__(self, input_dim=14, hidden_dim=128, output_dim=2):
        super(AeroSurrogateMLP, self).__init__()
        
        # Define the network architecture inside the object
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, output_dim) # Raw linear outputs for Cd and Cl
        )
        
    def forward(self, x):
        # Define how data passes through the model object
        return self.network(x)
    

def trainModel(model, optimizer, train_loader, test_loader, epochs=50, patience=5):
    criterion = nn.MSELoss()
    # optimizer = optim.Adam(model.parameters(), lr=0.001)

    
    patience_hit = False
    best_test_loss = float("inf")
    patience_counter = 0
    train_loss_history = []
    test_loss_history = []

    for epoch in range(epochs):
    # --- Training Step ---
        print(f"Epoch: {epoch}")
        model.train() # Tells PyTorch you are in training mode
        
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            batch_X = batch_X.to(device)
            batch_y = batch_y.to(device)

            predictions = model(batch_X) # Uses the object's forward pass
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_X.size(0)
            
        # --- Validation Step ---
        model.eval() # Tells PyTorch you are evaluating (turns off dropout, batchnorm etc.)
        test_loss = 0.0
        with torch.no_grad(): # Speeds up inference by skipping gradient calculation
            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(device)
                batch_y = batch_y.to(device)

                predictions = model(batch_X)
                if epoch == 0:
                    print("\n--- DEBUG FIRST EVAL BATCH ---")
                    print(f"Raw Preds (First 3): {predictions[:3].cpu().numpy()}")
                    print(f"Raw Targets (First 3): {batch_y[:3].cpu().numpy()}")
                    print("-------------------------------\n")

                loss = criterion(predictions, batch_y)
                test_loss += loss.item() * batch_X.size(0)
                
        # Calculate and display loss averages
        epoch_train_loss = train_loss / len(train_loader.dataset)
        epoch_test_loss = test_loss / len(test_loader.dataset)

        train_loss_history.append(epoch_train_loss)
        test_loss_history.append(epoch_test_loss)

        if epoch_test_loss < best_test_loss:
            best_test_loss = epoch_test_loss
            patience_counter = 0  # Reset the clock
            best_model_weights = copy.deepcopy(model.state_dict()) # Save snapshot of best weights
        else:
            patience_counter += 1
            # print(f"-> Test loss did not improve. Patience: {patience_counter}/{patience}")

        # Trigger early stop if patience runs out
        if patience_counter >= patience:
            # print(f"\nStopping early at epoch {epoch+1}. Test loss plateaued.")
            patience_hit = True
            break
    
    model.load_state_dict(best_model_weights)
    return model, train_loss_history, test_loss_history, patience_hit



if __name__ == "__main__":
    model = AeroSurrogateMLP().to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    data = pd.read_csv("sim_data.csv")

    patienceHit = False

    train_loss_data = []
    test_loss_data = []
    
    train_set, test_set, scaler_x, scaler_y = createSet(data)

    train_loader = DataLoader(train_set, batch_size=32, shuffle=True, pin_memory=True)
    test_loader = DataLoader(test_set, batch_size=32, shuffle=False, pin_memory=True)

    i = 1
    while not patienceHit:
        print(f"Iteration: {i}")
        model, train_loss, test_loss, patienceHit = trainModel(model, optimizer, train_loader, test_loader)
        train_loss_data.extend(train_loss)
        test_loss_data.extend(test_loss)
        i += 1
    
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'scaler_x': scaler_x,
        'scaler_y': scaler_y,
        'input_dim': 14,
        'hidden_dim': 128
    }

    joblib.dump(checkpoint, "model_weights.pth")

    x = range(len(train_loss_data))

    plt.plot(x, train_loss_data, 'r-', label="Training Loss")
    plt.plot(x, test_loss_data, 'b-', label="Eval Loss")
    plt.xlabel("Epochs")
    plt.ylabel("Mean Squared Error")

    plt.legend(loc='best', fontsize=10, frameon=True, facecolor='white', edgecolor='gray')

    plt.grid(True, linestyle=':', alpha=0.6)
    plt.savefig("my_plot.png", dpi=300, bbox_inches='tight')
    print("\nTraining completed. Plot saved as my_plot.png")
