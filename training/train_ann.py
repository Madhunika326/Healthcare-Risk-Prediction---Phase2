"""
ANN Regression Training for Healthcare Risk Prediction
========================================================

Phase 2: Train Artificial Neural Network (ANN) on hybrid features
  - Uses: Latent features (4-dim) + Original features (19-dim) = 23-dim input
  - Target: Health_Risk_Score (continuous regression)
  - Paper Requirement: Hybrid Autoencoder + ANN architecture
  
Methodology:
1. Load latent features from trained autoencoder
2. Load original preprocessed features
3. Concatenate: [latent_features] + [original_features]
4. Build ANN regression model: Input(23) → Hidden layers → Output(1)
5. Train on training set, evaluate on held-out test set
6. Save trained model and evaluation metrics
"""

import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)


def load_latent_features(train_path='models/latent_features_train.joblib',
                         test_path='models/latent_features_test.joblib'):
    """
    Load 4-dimensional latent features extracted by autoencoder.
    
    Returns:
    --------
    tuple
        (latent_train, latent_test) - Each of shape (n_samples, 4)
    """
    print("Loading latent features from autoencoder...")
    latent_train = joblib.load(train_path)
    latent_test = joblib.load(test_path)
    
    print(f"✓ Latent training features shape: {latent_train.shape}")
    print(f"✓ Latent test features shape: {latent_test.shape}")
    
    return latent_train, latent_test


def load_original_features(data_path='dataset/Final_Healthcare_Delay_Risk_Dataset.csv',
                           preprocessor_path='models/preprocessor.joblib'):
    """
    Load original preprocessed features (19-dimensional).
    
    Applies Age 18-60 filtering per research paper methodology.
    
    Returns:
    --------
    tuple
        (X_train, X_test, feature_names) 
        Each X of shape (n_samples, 19)
    """
    print("Loading original preprocessed features...")
    
    # Load dataset
    df = pd.read_csv(data_path)
    
    # CRITICAL: Filter to Age 18-60 per research paper methodology
    initial_rows = len(df)
    df = df[(df['Age'] >= 18) & (df['Age'] <= 60)]
    filtered_rows = len(df)
    print(f"Age filtering: {initial_rows} → {filtered_rows} samples (Age 18-60 only)")
    
    # Separate features (exclude both target and categorical target)
    X = df.drop(columns=['Health_Risk_Score'])
    if 'Risk_Category' in X.columns:
        X = X.drop(columns=['Risk_Category'])
    
    # Load preprocessor
    preprocessor = joblib.load(preprocessor_path)
    
    # Apply preprocessing
    X_processed = preprocessor.transform(X)
    X_processed = pd.DataFrame(X_processed, columns=preprocessor.get_feature_names_out())
    
    # Load train_test_split indices
    # NOTE: We must use the SAME split as autoencoder training for consistency
    from sklearn.model_selection import train_test_split
    X_np = X_processed.values.astype(np.float32)
    X_train, X_test = train_test_split(X_np, test_size=0.2, random_state=42)
    
    feature_names = preprocessor.get_feature_names_out()
    
    print(f"✓ Original training features shape: {X_train.shape}")
    print(f"✓ Original test features shape: {X_test.shape}")
    
    return X_train, X_test, feature_names


def load_target(data_path='dataset/Final_Healthcare_Delay_Risk_Dataset.csv'):
    """
    Load continuous target variable: Health_Risk_Score
    
    Applies Age 18-60 filtering per research paper methodology.
    
    Returns:
    --------
    tuple
        (y_train, y_test) - Each of shape (n_samples,)
    """
    print("Loading target variable (Health_Risk_Score)...")
    
    df = pd.read_csv(data_path)
    
    # CRITICAL: Filter to Age 18-60 per research paper methodology
    initial_rows = len(df)
    df = df[(df['Age'] >= 18) & (df['Age'] <= 60)]
    filtered_rows = len(df)
    print(f"Age filtering: {initial_rows} → {filtered_rows} samples (Age 18-60 only)")
    
    y = df['Health_Risk_Score'].values.astype(np.float32)
    
    # Use SAME train_test_split indices
    from sklearn.model_selection import train_test_split
    y_train, y_test = train_test_split(y, test_size=0.2, random_state=42)
    
    print(f"✓ Target training shape: {y_train.shape}")
    print(f"✓ Target test shape: {y_test.shape}")
    print(f"✓ Target range: [{y_train.min():.2f}, {y_train.max():.2f}]")
    
    return y_train, y_test


def concatenate_hybrid_features(latent_train, latent_test, X_train, X_test):
    """
    Concatenate latent features with original features.
    
    Creates hybrid input: [latent_4dim] + [original_19dim] = 23-dim
    
    Parameters:
    -----------
    latent_train, latent_test : np.ndarray
        4-dimensional latent features from autoencoder
    X_train, X_test : np.ndarray
        19-dimensional original preprocessed features
        
    Returns:
    --------
    tuple
        (X_hybrid_train, X_hybrid_test) - Each of shape (n_samples, 23)
    """
    print("\nCreating hybrid feature vectors...")
    
    # Ensure shapes match
    assert latent_train.shape[0] == X_train.shape[0], \
        f"Latent train ({latent_train.shape[0]}) != Original train ({X_train.shape[0]})"
    assert latent_test.shape[0] == X_test.shape[0], \
        f"Latent test ({latent_test.shape[0]}) != Original test ({X_test.shape[0]})"
    
    # Concatenate along feature axis
    X_hybrid_train = np.concatenate([latent_train, X_train], axis=1)
    X_hybrid_test = np.concatenate([latent_test, X_test], axis=1)
    
    print(f"✓ Hybrid training features shape: {X_hybrid_train.shape}")
    print(f"  └─ Composition: 4 latent + 19 original = 23 total")
    print(f"✓ Hybrid test features shape: {X_hybrid_test.shape}")
    
    return X_hybrid_train, X_hybrid_test


def build_ann_regressor(input_dim=23):
    """
    Build ANN regression model per research paper specifications.
    
    Architecture:
    - Input: 23 dimensions (4 latent + 19 original)
    - Hidden layer 1: Dense(64, relu) with batch normalization
    - Hidden layer 2: Dense(32, relu) with batch normalization
    - Hidden layer 3: Dense(16, relu)
    - Output: Dense(1, linear) - continuous Health_Risk_Score
    
    The architecture balances:
    - Capacity to learn non-linear relationships
    - Regularization to prevent overfitting
    - Interpretability through moderate layer sizes
    
    Parameters:
    -----------
    input_dim : int
        Number of input features (default: 23)
        
    Returns:
    --------
    tf.keras.Model
        Compiled ANN regression model
    """
    print("\nBuilding ANN Regression Model...")
    print(f"Input dimension: {input_dim}")
    
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),
        
        # Hidden layer 1: 64 units with batch normalization
        layers.Dense(64, activation='relu', name='dense_64'),
        layers.BatchNormalization(name='bn_64'),
        
        # Hidden layer 2: 32 units with batch normalization
        layers.Dense(32, activation='relu', name='dense_32'),
        layers.BatchNormalization(name='bn_32'),
        
        # Hidden layer 3: 16 units
        layers.Dense(16, activation='relu', name='dense_16'),
        
        # Output layer: 1 unit for regression (no activation = linear)
        layers.Dense(1, name='output_regression')
    ], name='ann_regressor')
    
    # Compile with MSE loss (standard for regression) and Adam optimizer
    model.compile(
        loss='mean_squared_error',
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        metrics=['mae']  # MAE for interpretable error metric
    )
    
    print("\n" + "="*60)
    print("ANN REGRESSION MODEL ARCHITECTURE")
    print("="*60)
    model.summary()
    
    return model


def train_ann(model, X_train, y_train, X_test, y_test, epochs=100, batch_size=16):
    """
    Train ANN regression model on hybrid features.
    
    Parameters:
    -----------
    model : tf.keras.Model
        Compiled ANN regressor
    X_train, y_train : np.ndarray
        Training features (23-dim) and target
    X_test, y_test : np.ndarray
        Validation/test features and target
    epochs : int
        Number of training epochs (default: 100)
    batch_size : int
        Training batch size (default: 16)
        
    Returns:
    --------
    history : tf.keras.callbacks.History
        Training history with loss and metrics
    """
    print("\n" + "="*60)
    print("TRAINING ANN REGRESSOR")
    print("="*60)
    print(f"Training samples: {X_train.shape[0]}")
    print(f"Validation samples: {X_test.shape[0]}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Optimizer: Adam (lr=0.001)")
    print(f"Loss: Mean Squared Error (MSE)")
    print("="*60 + "\n")
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=batch_size,
        verbose=1
    )
    
    return history


def evaluate_ann(model, X_train, y_train, X_test, y_test):
    """
    Evaluate ANN regression on both training and test sets.
    
    Computes:
    - MAE (Mean Absolute Error)
    - RMSE (Root Mean Squared Error)
    - R² (Coefficient of determination)
    
    Parameters:
    -----------
    model : tf.keras.Model
        Trained ANN regressor
    X_train, y_train : np.ndarray
        Training set
    X_test, y_test : np.ndarray
        Test set
        
    Returns:
    --------
    dict
        Dictionary of evaluation metrics
    """
    print("\n" + "="*60)
    print("EVALUATION & METRICS")
    print("="*60)
    
    # Predictions on training set
    print("\nEvaluating on TRAINING set...")
    y_train_pred = model.predict(X_train, verbose=0).flatten()
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_mse = mean_squared_error(y_train, y_train_pred)
    train_rmse = np.sqrt(train_mse)
    train_r2 = r2_score(y_train, y_train_pred)
    
    print(f"✓ Training MAE: {train_mae:.4f}")
    print(f"✓ Training RMSE: {train_rmse:.4f}")
    print(f"✓ Training R²: {train_r2:.4f}")
    
    # Predictions on test set
    print("\nEvaluating on TEST set...")
    y_test_pred = model.predict(X_test, verbose=0).flatten()
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    test_rmse = np.sqrt(test_mse)
    test_r2 = r2_score(y_test, y_test_pred)
    
    print(f"✓ Test MAE: {test_mae:.4f}")
    print(f"✓ Test RMSE: {test_rmse:.4f}")
    print(f"✓ Test R²: {test_r2:.4f}")
    
    # Compute differences (generalization gap)
    mae_gap = test_mae - train_mae
    rmse_gap = test_rmse - train_rmse
    r2_gap = train_r2 - test_r2
    
    print("\n" + "-"*60)
    print("GENERALIZATION GAP (Test - Train)")
    print("-"*60)
    print(f"MAE gap: {mae_gap:.4f} ({'✓ Good' if abs(mae_gap) < 0.05 else '⚠ Monitor'})")
    print(f"RMSE gap: {rmse_gap:.4f}")
    print(f"R² gap: {r2_gap:.4f} ({'✓ Good' if r2_gap < 0.05 else '⚠ Monitor'})")
    
    metrics = {
        'train_mae': float(train_mae),
        'train_rmse': float(train_rmse),
        'train_r2': float(train_r2),
        'test_mae': float(test_mae),
        'test_rmse': float(test_rmse),
        'test_r2': float(test_r2),
        'mae_gap': float(mae_gap),
        'rmse_gap': float(rmse_gap),
        'r2_gap': float(r2_gap)
    }
    
    return metrics


def save_models_and_metrics(model, metrics, model_path='models/ann_model.keras',
                            metrics_path='models/ann_metrics.json'):
    """
    Save trained ANN model and evaluation metrics.
    
    Parameters:
    -----------
    model : tf.keras.Model
        Trained ANN regressor
    metrics : dict
        Evaluation metrics dictionary
    model_path : str
        Path to save model
    metrics_path : str
        Path to save metrics as JSON
    """
    print("\n" + "-"*60)
    print("SAVING MODELS & METRICS")
    print("-"*60)
    
    # Save model
    model.save(model_path)
    print(f"✓ ANN model saved to: {model_path}")
    
    # Save metrics as JSON
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Evaluation metrics saved to: {metrics_path}")


def main():
    """
    Main workflow: Load features → Build model → Train → Evaluate → Save
    """
    print("\n" + "="*60)
    print("HEALTHCARE RISK PREDICTION - ANN TRAINING")
    print("="*60)
    
    # STEP 1: Load all required data
    print("\nSTEP 1: Loading Data & Features")
    print("-"*60)
    
    latent_train, latent_test = load_latent_features()
    X_train, X_test, feature_names = load_original_features()
    y_train, y_test = load_target()
    
    # STEP 2: Create hybrid features
    print("\nSTEP 2: Creating Hybrid Features")
    print("-"*60)
    
    X_hybrid_train, X_hybrid_test = concatenate_hybrid_features(
        latent_train, latent_test, X_train, X_test
    )
    
    # STEP 3: Build ANN model
    print("\nSTEP 3: Building ANN Regression Model")
    print("-"*60)
    
    model = build_ann_regressor(input_dim=X_hybrid_train.shape[1])
    
    # STEP 4: Train ANN
    print("\nSTEP 4: Training ANN Regressor")
    print("-"*60)
    
    history = train_ann(
        model, X_hybrid_train, y_train, X_hybrid_test, y_test,
        epochs=100, batch_size=16
    )
    
    # STEP 5: Evaluate and save
    print("\nSTEP 5: Evaluation & Model Saving")
    print("-"*60)
    
    metrics = evaluate_ann(model, X_hybrid_train, y_train, X_hybrid_test, y_test)
    save_models_and_metrics(model, metrics)
    
    # Final summary
    print("\n" + "="*60)
    print("✓ ANN TRAINING COMPLETE!")
    print("="*60)
    print("\nArtifacts saved:")
    print("  - models/ann_model.keras (trained regressor)")
    print("  - models/ann_metrics.json (evaluation metrics)")
    print("\nModel Performance Summary:")
    print(f"  - Test MAE: {metrics['test_mae']:.4f}")
    print(f"  - Test RMSE: {metrics['test_rmse']:.4f}")
    print(f"  - Test R²: {metrics['test_r2']:.4f}")
    print("\nReady for next phase: Flask Web Application")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
