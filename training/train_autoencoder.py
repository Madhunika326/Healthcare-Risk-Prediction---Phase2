import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from pathlib import Path
from sklearn.model_selection import train_test_split

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

def load_and_preprocess_data(data_path='dataset/Final_Healthcare_Delay_Risk_Dataset.csv',
                             preprocessor_path='models/preprocessor.joblib'):
    """
    Load data, filter to Age 18-60, and apply preprocessing pipeline.
    
    Paper Methodology:
    - Original synthetic dataset: 6000 samples
    - Filtered to Age 18-60: ~3836 samples (REQUIRED for paper reproduction)
    
    Returns ONLY features (X), not target (y), since autoencoder is unsupervised.
    
    Parameters:
    -----------
    data_path : str
        Path to raw dataset CSV
    preprocessor_path : str
        Path to fitted preprocessor (ColumnTransformer)
        
    Returns:
    --------
    np.ndarray
        Preprocessed feature matrix (float32)
    """
    print("Loading dataset...")
    df = pd.read_csv(data_path)
    initial_rows = len(df)
    
    # CRITICAL: Filter to Age 18-60 per research paper methodology
    df = df[(df['Age'] >= 18) & (df['Age'] <= 60)]
    filtered_rows = len(df)
    print(f"Age filtering: {initial_rows} → {filtered_rows} samples (Age 18-60 only)")
    
    # Separate features and target
    # CRITICAL: Exclude both Health_Risk_Score (target) and Risk_Category (categorical target)
    X = df.drop(columns=['Health_Risk_Score'])
    
    # Remove Risk_Category from features (it's derived from target, causes data leakage)
    if 'Risk_Category' in X.columns:
        X = X.drop(columns=['Risk_Category'])
    
    print(f"Features shape before preprocessing: {X.shape}")
    
    # Load preprocessor
    print("Loading preprocessor...")
    preprocessor = joblib.load(preprocessor_path)
    
    # Apply preprocessing (same transformations as training preprocessing)
    X_processed = preprocessor.transform(X)
    X_processed = pd.DataFrame(X_processed, columns=preprocessor.get_feature_names_out())
    
    print(f"Features shape after preprocessing: {X_processed.shape}")
    print(f"Number of features: {X_processed.shape[1]}")
    
    return X_processed.values.astype(np.float32)


def build_autoencoder(input_dim):
    """
    Build encoder and full autoencoder models according to research paper specifications.
    
    Architecture:
    - Encoder: Input → Dense(16, relu) → Dense(8, relu) → Dense(4, relu)
      └─ Bottleneck dimension: 4 (latent features)
    - Decoder: Dense(8, relu) → Dense(16, relu) → Output (linear)
    
    The encoder learns a low-dimensional representation (4-dim latent space).
    This latent representation captures the essential features of the healthcare data.
    
    Parameters:
    -----------
    input_dim : int
        Number of input features (auto-detected from preprocessed data)
        
    Returns:
    --------
    tuple
        (autoencoder, encoder)
        - autoencoder: Full model for training (input -> encode -> decode -> output)
        - encoder: Encoder model only (input -> latent 4-dim output)
    """
    print(f"\nBuilding Autoencoder with input dimension: {input_dim}")
    
    # ===== ENCODER =====
    # Compresses input features to 4-dimensional latent representation
    encoder_input = layers.Input(shape=(input_dim,))
    encoded = layers.Dense(16, activation='relu', name='encoder_dense1')(encoder_input)
    encoded = layers.Dense(8, activation='relu', name='encoder_dense2')(encoded)
    encoded_output = layers.Dense(4, activation='relu', name='latent_bottleneck')(encoded)
    
    encoder = Model(encoder_input, encoded_output, name='encoder')
    print(f"✓ Encoder output dimension: 4 (latent bottleneck)")
    
    # ===== DECODER =====
    # Reconstructs original features from 4-dimensional latent representation
    decoder_input = layers.Input(shape=(4,))
    decoded = layers.Dense(8, activation='relu', name='decoder_dense1')(decoder_input)
    decoded = layers.Dense(16, activation='relu', name='decoder_dense2')(decoded)
    decoded_output = layers.Dense(input_dim, activation='linear', name='reconstruction')(decoded)
    
    decoder = Model(decoder_input, decoded_output, name='decoder')
    print(f"✓ Decoder reconstructs to input dimension: {input_dim}")
    
    # ===== FULL AUTOENCODER =====
    # Combines encoder and decoder for end-to-end training
    autoencoder_input = layers.Input(shape=(input_dim,))
    encoded = encoder(autoencoder_input)
    decoded = decoder(encoded)
    
    autoencoder = Model(autoencoder_input, decoded, name='autoencoder')
    
    return autoencoder, encoder


def train_autoencoder(X_train, X_val, autoencoder, epochs=50, batch_size=16):
    """
    Compile and train the autoencoder on training data.
    
    Training Configuration (from research paper):
    - Loss: Mean Squared Error (MSE) - measures reconstruction quality
    - Optimizer: Adam - adaptive learning rate
    - Epochs: 50 - iterations over full dataset
    - Batch size: 16 - samples per gradient update
    - Validation set: Used to monitor overfitting during training
    
    Parameters:
    -----------
    X_train : np.ndarray
        Training features (80% of data)
    X_val : np.ndarray
        Validation features (20% of data) - used to monitor training
    autoencoder : Model
        Compiled Keras autoencoder model
    epochs : int
        Number of training epochs
    batch_size : int
        Batch size for training
        
    Returns:
    --------
    History
        Training history with loss metrics
    """
    print("\n" + "="*60)
    print("TRAINING AUTOENCODER")
    print("="*60)
    print(f"Compiling Autoencoder with:")
    print(f"  - Loss: Mean Squared Error (MSE)")
    print(f"  - Optimizer: Adam")
    print(f"  - Epochs: {epochs}")
    print(f"  - Batch size: {batch_size}")
    print("="*60)
    
    autoencoder.compile(optimizer='adam', loss='mse')
    
    print(f"\nTraining on {X_train.shape[0]} samples...")
    print(f"Validating on {X_val.shape[0]} samples...\n")
    
    # Train autoencoder to reconstruct its input
    # Target is X_train itself (unsupervised learning)
    history = autoencoder.fit(
        X_train, X_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_val, X_val),  # Use explicit validation set
        verbose=1
    )
    
    return history


def extract_latent_features(X, encoder):
    """
    Extract latent features (4-dimensional bottleneck representation) from encoder.
    
    The encoder compresses the input features into a 4-dimensional latent space.
    These latent features capture the essential information about healthcare risk.
    They will be concatenated with original features for ANN training.
    
    Parameters:
    -----------
    X : np.ndarray
        Input features (shape: n_samples, n_features)
    encoder : Model
        Trained encoder model
        
    Returns:
    --------
    np.ndarray
        Latent features (shape: n_samples, 4)
    """
    print(f"Extracting latent features from {X.shape[0]} samples...")
    latent_features = encoder.predict(X, verbose=0)
    print(f"✓ Latent features shape: {latent_features.shape}")
    return latent_features


def evaluate_and_save(X_train, X_test, autoencoder, encoder,
                      autoencoder_path='models/autoencoder.keras',
                      encoder_path='models/encoder.keras',
                      latent_train_path='models/latent_features_train.joblib',
                      latent_test_path='models/latent_features_test.joblib'):
    """
    Evaluate reconstruction loss on train and test sets.
    Extract and save latent features for both sets.
    Save trained models.
    
    Paper Requirements Fulfilled:
    - ✓ Extract latent features from encoder only (paper req #9)
    - ✓ Save encoder model (paper req #10)
    - ✓ Save latent features for train and test sets (paper req #11)
    
    Parameters:
    -----------
    X_train : np.ndarray
        Training features
    X_test : np.ndarray
        Test features
    autoencoder : Model
        Trained autoencoder model
    encoder : Model
        Trained encoder model
    autoencoder_path : str
        Where to save autoencoder model
    encoder_path : str
        Where to save encoder model
    latent_train_path : str
        Where to save training latent features
    latent_test_path : str
        Where to save test latent features
        
    Returns:
    --------
    tuple
        (latent_train, latent_test, train_loss, test_loss)
    """
    print("\n" + "="*60)
    print("EVALUATION & FEATURE EXTRACTION")
    print("="*60)
    
    # Calculate reconstruction loss on TRAINING set
    print("\nEvaluating on TRAINING set...")
    train_reconstructions = autoencoder.predict(X_train, verbose=0)
    train_loss = np.mean(np.square(X_train - train_reconstructions))
    train_rmse = np.sqrt(train_loss)
    
    print(f"✓ Training MSE (Reconstruction Loss): {train_loss:.6f}")
    print(f"✓ Training RMSE: {train_rmse:.6f}")
    
    # Calculate reconstruction loss on TEST set
    print("\nEvaluating on TEST set...")
    test_reconstructions = autoencoder.predict(X_test, verbose=0)
    test_loss = np.mean(np.square(X_test - test_reconstructions))
    test_rmse = np.sqrt(test_loss)
    
    print(f"✓ Test MSE (Reconstruction Loss): {test_loss:.6f}")
    print(f"✓ Test RMSE: {test_rmse:.6f}")
    
    # Extract latent features
    print("\n" + "-"*60)
    print("LATENT FEATURE EXTRACTION")
    print("-"*60)
    
    latent_train = extract_latent_features(X_train, encoder)
    latent_test = extract_latent_features(X_test, encoder)
    
    # Create models directory if it doesn't exist
    Path('models').mkdir(exist_ok=True)
    
    # Save models
    print("\n" + "-"*60)
    print("SAVING MODELS")
    print("-"*60)
    
    autoencoder.save(autoencoder_path)
    print(f"✓ Autoencoder saved to: {autoencoder_path}")
    
    encoder.save(encoder_path)
    print(f"✓ Encoder saved to: {encoder_path}")
    
    # Save latent features
    print("\n" + "-"*60)
    print("SAVING LATENT FEATURES")
    print("-"*60)
    
    joblib.dump(latent_train, latent_train_path)
    print(f"✓ Training latent features saved to: {latent_train_path}")
    
    joblib.dump(latent_test, latent_test_path)
    print(f"✓ Test latent features saved to: {latent_test_path}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Training Reconstruction Loss (MSE): {train_loss:.6f}")
    print(f"Test Reconstruction Loss (MSE): {test_loss:.6f}")
    print(f"Latent Dimensionality: 4 (bottleneck)")
    print(f"Training Samples: {X_train.shape[0]}, Test Samples: {X_test.shape[0]}")
    print("="*60)
    
    return latent_train, latent_test, train_loss, test_loss


def main():
    """
    Main autoencoder training pipeline.
    
    Workflow:
    1. Load and preprocess healthcare dataset
    2. Split into train (80%) and test (20%) sets
    3. Build autoencoder model with 4-dimensional bottleneck
    4. Train autoencoder on training data
    5. Evaluate reconstruction loss on both train and test sets
    6. Extract latent features from encoder
    7. Save all models and latent features for next phase (ANN training)
    """
    print("="*60)
    print("HEALTHCARE RISK PREDICTION - AUTOENCODER TRAINING")
    print("="*60)
    
    # Step 1: Load and preprocess data
    print("\nSTEP 1: Loading and Preprocessing Data")
    print("-"*60)
    X = load_and_preprocess_data()
    
    # Step 2: Train/test split (80/20)
    print("\nSTEP 2: Train/Test Split")
    print("-"*60)
    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42)
    print(f"Training set size: {X_train.shape[0]} samples")
    print(f"Test set size: {X_test.shape[0]} samples")
    
    # Auto-detect input dimension from training data
    input_dim = X_train.shape[1]
    print(f"Input dimension: {input_dim}")
    
    # Step 3: Build models
    print("\nSTEP 3: Building Autoencoder Architecture")
    print("-"*60)
    autoencoder, encoder = build_autoencoder(input_dim)
    
    # Print model summaries
    print("\n" + "-"*60)
    print("ENCODER ARCHITECTURE")
    print("-"*60)
    encoder.summary()
    
    print("\n" + "-"*60)
    print("FULL AUTOENCODER ARCHITECTURE")
    print("-"*60)
    autoencoder.summary()
    
    # Step 4: Train autoencoder
    print("\nSTEP 4: Training Autoencoder")
    print("-"*60)
    history = train_autoencoder(X_train, X_test, autoencoder, epochs=50, batch_size=16)
    
    # Step 5 & 6 & 7: Evaluate, extract latent features, and save
    print("\nSTEP 5: Evaluation, Feature Extraction & Model Saving")
    print("-"*60)
    latent_train, latent_test, train_loss, test_loss = evaluate_and_save(
        X_train, X_test, autoencoder, encoder
    )
    
    print("\n" + "="*60)
    print("✓ AUTOENCODER TRAINING COMPLETE!")
    print("="*60)
    print("\nArtifacts saved:")
    print("  - models/autoencoder.keras (full model)")
    print("  - models/encoder.keras (encoder only)")
    print("  - models/latent_features_train.joblib (4-dim latent for train set)")
    print("  - models/latent_features_test.joblib (4-dim latent for test set)")
    print("\nReady for next phase: ANN Regression Training")
    print("="*60)


if __name__ == '__main__':
    main()