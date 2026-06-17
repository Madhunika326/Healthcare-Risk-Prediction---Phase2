"""
Healthcare Delay Risk Prediction - Data Preprocessing Module

This module handles data preprocessing for the healthcare delay risk prediction model.
It performs the following operations:
1. Loads the dataset
2. Handles categorical variables using OneHotEncoder
3. Standardizes numerical features using StandardScaler
4. Saves the fitted transformers using joblib
5. Returns processed features and target variable
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def load_dataset(data_path: str) -> pd.DataFrame:
    """
    Load the healthcare delay risk dataset and filter to Age 18-60.
    
    Per research paper methodology:
    - Original synthetic dataset: 6000 samples
    - Filtered to Age 18-60: 3836 samples (used for model training)
    
    Parameters:
    -----------
    data_path : str
        Path to the CSV file containing the dataset
        
    Returns:
    --------
    pd.DataFrame
        Loaded and age-filtered dataset (Age 18-60 only)
    """
    df = pd.read_csv(data_path)
    print(f"Dataset loaded. Shape: {df.shape}")
    
    # CRITICAL: Filter to Age 18-60 per research paper methodology
    initial_rows = len(df)
    df = df[(df['Age'] >= 18) & (df['Age'] <= 60)]
    filtered_rows = len(df)
    
    print(f"After Age 18-60 filtering: {filtered_rows} rows (removed {initial_rows - filtered_rows} rows)")
    print(f"Dataset shape after filtering: {df.shape}")
    
    return df


def identify_feature_types(df: pd.DataFrame, target_col: str = 'Health_Risk_Score') -> tuple:
    """
    Identify categorical and numerical features in the dataset.
    
    CRITICAL: Excludes both target column AND Risk_Category (which is derived from target).
    Risk_Category must never be used as an input feature to avoid data leakage.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
    target_col : str
        Name of the target column
        
    Returns:
    --------
    tuple
        (numerical_features, categorical_features)
    """
    # Separate features, excluding both target and Risk_Category
    # Risk_Category is derived from Health_Risk_Score and must NOT be used as input feature
    X = df.drop(columns=[target_col, 'Risk_Category'])
    
    # Identify categorical and numerical columns
    categorical_features = X.select_dtypes(include=['object', 'bool']).columns.tolist()
    numerical_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    return numerical_features, categorical_features


def preprocess_data(data_path: str, 
                   target_col: str = 'Health_Risk_Score',
                   scaler_path: str = 'models/scaler.joblib',
                   encoder_path: str = 'models/encoder.joblib') -> tuple:
    """
    Preprocess the healthcare dataset by handling categorical variables and scaling numerical features.
    
    Parameters:
    -----------
    data_path : str
        Path to the CSV file containing the dataset
    target_col : str
        Name of the target column (default: 'Health_Risk_Score')
    scaler_path : str
        Path to save the fitted StandardScaler (default: 'models/scaler.joblib')
    encoder_path : str
        Path to save the fitted OneHotEncoder (default: 'models/encoder.joblib')
        
    Returns:
    --------
    tuple
        (X_processed, y, scaler, encoder, feature_names)
        - X_processed: Preprocessed feature matrix
        - y: Target variable
        - scaler: Fitted StandardScaler object
        - encoder: Fitted OneHotEncoder object
        - feature_names: Names of the processed features
    """
    
    # Load dataset
    df = load_dataset(data_path)
    
    # Separate features and target
    # CRITICAL: Exclude Risk_Category from features (it's derived from target, causes data leakage)
    X = df.drop(columns=[target_col, 'Risk_Category'])
    y = df[target_col]
    
    # Identify feature types
    numerical_features, categorical_features = identify_feature_types(df, target_col)
    
    print(f"\nNumerical features ({len(numerical_features)}): {numerical_features}")
    print(f"Categorical features ({len(categorical_features)}): {categorical_features}")
    
    # Create preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numerical_features),
            ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), categorical_features)
        ],
        remainder='passthrough'
    )
    
    # Fit and transform the data
    X_processed = preprocessor.fit_transform(X)
    
    # Extract the fitted scaler and encoder
    scaler = preprocessor.named_transformers_['num']
    encoder = preprocessor.named_transformers_['cat']
    
    # Get feature names directly from the fitted ColumnTransformer
    # This is more reliable than manually concatenating feature lists
    feature_names = preprocessor.get_feature_names_out().tolist()
    
    # Convert to dataframe for easier handling
    X_processed = pd.DataFrame(X_processed, columns=feature_names)
    
    print(f"\nPreprocessing complete!")
    print(f"Processed features shape: {X_processed.shape}")
    print(f"Target shape: {y.shape}")
    
    # Create models directory if it doesn't exist
    models_dir = Path(scaler_path).parent
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the transformers
    joblib.dump(scaler, scaler_path)
    joblib.dump(encoder, encoder_path)
    joblib.dump(preprocessor, 'models/preprocessor.joblib')
    
    print(f"\nTransformers saved:")
    print(f"  - Scaler: {scaler_path}")
    print(f"  - Encoder: {encoder_path}")
    print(f"  - Full preprocessor: models/preprocessor.joblib")
    
    return X_processed, y, scaler, encoder, feature_names


def preprocess_new_data(new_data: pd.DataFrame,
                        preprocessor_path: str = 'models/preprocessor.joblib') -> pd.DataFrame:
    """
    Preprocess new data using the previously fitted preprocessor pipeline.
    
    This function ensures consistency by using the exact same transformations
    that were applied during training. It avoids duplicating transformation logic.
    
    Parameters:
    -----------
    new_data : pd.DataFrame
        New dataset to preprocess (without target column)
    preprocessor_path : str
        Path to the saved ColumnTransformer preprocessor
        
    Returns:
    --------
    pd.DataFrame
        Preprocessed feature matrix
    """
    
    # Load the fitted preprocessor (contains all transformation logic)
    preprocessor = joblib.load(preprocessor_path)
    
    # Apply the preprocessor to new data
    # This ensures the exact same transformations as training data
    X_processed = preprocessor.transform(new_data)
    
    # Get feature names from the preprocessor
    feature_names = preprocessor.get_feature_names_out().tolist()
    
    # Convert to dataframe
    X_processed = pd.DataFrame(X_processed, columns=feature_names)
    
    return X_processed


if __name__ == "__main__":
    # Example usage
    import os
    
    # Define paths
    dataset_path = "dataset/Final_Healthcare_Delay_Risk_Dataset.csv"
    scaler_path = "models/scaler.joblib"
    encoder_path = "models/encoder.joblib"
    
    # Check if dataset exists
    if os.path.exists(dataset_path):
        # Preprocess the data
        X_processed, y, scaler, encoder, feature_names = preprocess_data(
            data_path=dataset_path,
            scaler_path=scaler_path,
            encoder_path=encoder_path
        )
        
        print(f"\nFirst few rows of processed data:")
        print(X_processed.head())
        
        print(f"\nTarget variable statistics:")
        print(y.describe())
    else:
        print(f"Dataset not found at {dataset_path}")

    
