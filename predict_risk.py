"""
Healthcare Risk Prediction - Phase 3: Prediction Pipeline

This module provides a complete prediction pipeline for the Healthcare Risk Prediction system.

Workflow:
1. Load pre-trained models (preprocessor, autoencoder encoder, ANN regressor)
2. Accept raw user input features
3. Validate input ranges
4. Apply preprocessing (scaling + encoding)
5. Extract latent features using trained encoder
6. Create hybrid features (latent + original)
7. Predict Health_Risk_Score using ANN
8. Categorize into Low/Medium/High Risk

Output Format:
{
    "health_risk_score": float,
    "risk_category": str ("Low Risk" | "Medium Risk" | "High Risk"),
    "prediction_details": dict with intermediate values
}
"""

import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from pathlib import Path
from typing import Dict, Tuple, Any
import json


# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

class RiskConfig:
    """Configuration for risk prediction system."""
    
    # Model paths - absolute based on predict_risk.py location
    BASE_DIR = Path(__file__).resolve().parent
    MODEL_DIR = BASE_DIR / 'models'
    PREPROCESSOR_PATH = MODEL_DIR / 'preprocessor.joblib'
    ENCODER_PATH = MODEL_DIR / 'encoder.keras'
    ANN_MODEL_PATH = MODEL_DIR / 'ann_model.keras'
    ANN_METRICS_PATH = MODEL_DIR / 'ann_metrics.json'
    
    # Risk category thresholds (per research paper)
    LOW_RISK_THRESHOLD = 35.0
    MEDIUM_RISK_THRESHOLD = 65.0
    # High Risk: >= 65
    
    # INPUT VALIDATION RANGES - RAW DATASET VALUES (Age 18-60 Filtered Data)
    # CRITICAL: These are the ORIGINAL dataset ranges, NOT standardized values
    # Users input RAW values here; preprocessing applies StandardScaler internally
    VALID_RANGES = {
        'Age': (18, 60),                        # Years
        'Health_Awareness_Score': (1, 5),      # 1-5 scale (mean: 3.01)
        'Symptom_Severity': (1, 5),            # 1-5 scale (mean: 2.99)
        'Distance_to_Healthcare_km': (1, 49),  # Kilometers (mean: 24.85)
        'Fear_of_Cost': (0, 1),                # 0-1 binary/continuous (mean: 0.40)
        'Fear_of_Hospital': (0, 1),            # 0-1 binary/continuous (mean: 0.31)
        'Delay_in_Seeking_Care_Days': (0, 119), # Days (mean: 59.72)
    }
    
    # CATEGORICAL FEATURES - Valid categories from dataset (Age 18-60 filtered)
    # CRITICAL: Must match exact values in the dataset
    VALID_CATEGORIES = {
        'Gender': ['Male', 'Female'],
        'Residence': ['Urban', 'Rural'],
        'Education_Level': ['High', 'Low', 'Medium'],  # NOT 'High School', 'Bachelor', etc.
        'Income_Level': ['Low', 'Middle', 'High'],     # Use 'Middle' not 'Medium'
        'Insurance_Status': ['Insured', 'Uninsured'],
    }


# ============================================================
# MODEL LOADING & INITIALIZATION
# ============================================================

class ModelLoader:
    """Handles loading and caching of pre-trained models."""
    
    _models_cache = {}
    
    @classmethod
    def load_models(cls) -> Dict[str, Any]:
        """
        Load all required models from disk.
        
        Returns:
        --------
        dict
            Dictionary containing:
            - 'preprocessor': ColumnTransformer for feature preprocessing
            - 'encoder': Keras model for latent feature extraction
            - 'ann_model': Keras model for risk score prediction
            - 'metrics': JSON dict with training metrics
            
        Raises:
        -------
        FileNotFoundError
            If any required model file is missing
        """
        if cls._models_cache:
            print("✓ Using cached models")
            return cls._models_cache
        
        print("Loading pre-trained models...")
        models = {}
        
        try:
            # Load preprocessor
            if not RiskConfig.PREPROCESSOR_PATH.exists():
                raise FileNotFoundError(f"Preprocessor not found: {RiskConfig.PREPROCESSOR_PATH}")
            models['preprocessor'] = joblib.load(RiskConfig.PREPROCESSOR_PATH)
            print(f"  ✓ Preprocessor loaded: {RiskConfig.PREPROCESSOR_PATH}")
            
            # Load encoder for latent feature extraction
            if not RiskConfig.ENCODER_PATH.exists():
                raise FileNotFoundError(f"Encoder not found: {RiskConfig.ENCODER_PATH}")
            models['encoder'] = tf.keras.models.load_model(RiskConfig.ENCODER_PATH)
            print(f"  ✓ Encoder loaded: {RiskConfig.ENCODER_PATH}")
            
            # Load ANN regressor model
            if not RiskConfig.ANN_MODEL_PATH.exists():
                raise FileNotFoundError(f"ANN model not found: {RiskConfig.ANN_MODEL_PATH}")
            models['ann_model'] = tf.keras.models.load_model(RiskConfig.ANN_MODEL_PATH)
            print(f"  ✓ ANN model loaded: {RiskConfig.ANN_MODEL_PATH}")
            
            # Load metrics (optional, for reference)
            if RiskConfig.ANN_METRICS_PATH.exists():
                with open(RiskConfig.ANN_METRICS_PATH, 'r') as f:
                    models['metrics'] = json.load(f)
                print(f"  ✓ Metrics loaded: {RiskConfig.ANN_METRICS_PATH}")
            else:
                models['metrics'] = {}
                print(f"  ⚠ Metrics file not found: {RiskConfig.ANN_METRICS_PATH}")
            
            cls._models_cache = models
            print("✓ All models loaded successfully!\n")
            return models
            
        except Exception as e:
            raise RuntimeError(f"Error loading models: {str(e)}")


# ============================================================
# INPUT VALIDATION
# ============================================================

class InputValidator:
    """Validates user input features."""
    
    @staticmethod
    def validate_numerical_feature(feature_name: str, value: float) -> Tuple[bool, str]:
        """
        Validate a numerical feature against valid range.
        
        Returns:
        --------
        tuple
            (is_valid: bool, message: str)
        """
        if feature_name not in RiskConfig.VALID_RANGES:
            return False, f"Unknown feature: {feature_name}"
        
        min_val, max_val = RiskConfig.VALID_RANGES[feature_name]
        
        if not isinstance(value, (int, float)):
            return False, f"{feature_name} must be numeric, got {type(value).__name__}"
        
        if value < min_val or value > max_val:
            return False, f"{feature_name} = {value} out of range [{min_val}, {max_val}]"
        
        return True, ""
    
    @staticmethod
    def validate_categorical_feature(feature_name: str, value: str) -> Tuple[bool, str]:
        """
        Validate a categorical feature against valid categories.
        
        Returns:
        --------
        tuple
            (is_valid: bool, message: str)
        """
        if feature_name not in RiskConfig.VALID_CATEGORIES:
            return False, f"Unknown categorical feature: {feature_name}"
        
        valid_categories = RiskConfig.VALID_CATEGORIES[feature_name]
        
        if value not in valid_categories:
            return False, f"{feature_name} = '{value}' not in {valid_categories}"
        
        return True, ""
    
    @staticmethod
    def validate_input(input_dict: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate complete input dictionary.
        
        Parameters:
        -----------
        input_dict : dict
            Dictionary with all required features
            
        Returns:
        --------
        tuple
            (is_valid: bool, error_message: str)
        """
        # Required numerical features
        numerical_features = [
            'Age', 'Health_Awareness_Score', 'Symptom_Severity',
            'Distance_to_Healthcare_km', 'Fear_of_Cost', 'Fear_of_Hospital',
            'Delay_in_Seeking_Care_Days'
        ]
        
        # Required categorical features
        categorical_features = [
            'Gender', 'Residence', 'Education_Level', 'Income_Level', 'Insurance_Status'
        ]
        
        # Check all numerical features present
        for feat in numerical_features:
            if feat not in input_dict:
                return False, f"Missing numerical feature: {feat}"
            
            is_valid, msg = InputValidator.validate_numerical_feature(feat, input_dict[feat])
            if not is_valid:
                return False, msg
        
        # Check all categorical features present
        for feat in categorical_features:
            if feat not in input_dict:
                return False, f"Missing categorical feature: {feat}"
            
            is_valid, msg = InputValidator.validate_categorical_feature(feat, input_dict[feat])
            if not is_valid:
                return False, msg
        
        return True, ""


# ============================================================
# FEATURE PROCESSING
# ============================================================

class FeatureProcessor:
    """Handles feature preprocessing and latent feature extraction."""
    
    @staticmethod
    def preprocess_input(input_dict: Dict[str, Any], preprocessor) -> np.ndarray:
        """
        Preprocess raw input features using fitted preprocessor.
        
        CRITICAL WORKFLOW:
        1. User inputs RAW dataset values (original ranges, NOT standardized)
        2. Features are converted to DataFrame
        3. ColumnTransformer applies:
           - StandardScaler to numerical features (centers & scales)
           - OneHotEncoder to categorical features
        4. Result: 19 processed features ready for autoencoder
        
        Parameters:
        -----------
        input_dict : dict
            Raw user input with original dataset values:
            - Age: 18-60
            - Health_Awareness_Score: 1-5
            - Symptom_Severity: 1-5
            - Distance_to_Healthcare_km: 1-49
            - Fear_of_Cost: 0-1
            - Fear_of_Hospital: 0-1
            - Delay_in_Seeking_Care_Days: 0-119
            - Categorical: Gender, Residence, Education_Level, Income_Level, Insurance_Status
            
        preprocessor : sklearn ColumnTransformer
            Fitted preprocessor from training (contains StandardScaler + OneHotEncoder)
            
        Returns:
        --------
        np.ndarray
            Preprocessed feature matrix of shape (1, 19)
            - Values are STANDARDIZED (mean=0, std=1) for numerical features
            - Values are ONE-HOT ENCODED for categorical features
            
        Raises:
        -------
        ValueError
            If preprocessing fails
        """
        try:
            # Convert input dictionary to DataFrame
            df = pd.DataFrame([input_dict])
            
            # Get feature order from preprocessor
            # Note: preprocessor expects features in specific order
            feature_names = [
                'Age', 'Health_Awareness_Score', 'Symptom_Severity',
                'Distance_to_Healthcare_km', 'Fear_of_Cost', 'Fear_of_Hospital',
                'Delay_in_Seeking_Care_Days',
                'Gender', 'Residence', 'Education_Level', 'Income_Level', 'Insurance_Status'
            ]
            
            # Reorder DataFrame columns to match preprocessor expectations
            df = df[feature_names]
            
            # Apply preprocessing (StandardScaler + OneHotEncoder)
            X_processed = preprocessor.transform(df)
            
            return X_processed.astype(np.float32)
            
        except Exception as e:
            raise ValueError(f"Error during preprocessing: {str(e)}")
    
    @staticmethod
    def extract_latent_features(X_processed: np.ndarray, encoder) -> np.ndarray:
        """
        Extract latent features using trained encoder.
        
        Parameters:
        -----------
        X_processed : np.ndarray
            Preprocessed features of shape (1, 19)
        encoder : keras.Model
            Trained encoder model
            
        Returns:
        --------
        np.ndarray
            Latent features of shape (1, 4)
        """
        try:
            latent_features = encoder.predict(X_processed, verbose=0)
            return latent_features.astype(np.float32)
        except Exception as e:
            raise RuntimeError(f"Error extracting latent features: {str(e)}")
    
    @staticmethod
    def create_hybrid_features(latent_features: np.ndarray, X_processed: np.ndarray) -> np.ndarray:
        """
        Create hybrid feature matrix by concatenating latent and original features.
        
        Hybrid features = [latent (4-dim)] + [original (19-dim)] = 23-dim total
        
        Parameters:
        -----------
        latent_features : np.ndarray
            Latent features of shape (1, 4)
        X_processed : np.ndarray
            Preprocessed original features of shape (1, 19)
            
        Returns:
        --------
        np.ndarray
            Hybrid features of shape (1, 23)
        """
        hybrid_features = np.concatenate([latent_features, X_processed], axis=1)
        return hybrid_features.astype(np.float32)


# ============================================================
# RISK PREDICTION
# ============================================================

class RiskPredictor:
    """Main prediction engine."""
    
    def __init__(self):
        """Initialize predictor with loaded models."""
        self.models = ModelLoader.load_models()
    
    def predict_risk(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete prediction pipeline: validate → preprocess → latent → predict → categorize
        
        Parameters:
        -----------
        input_dict : dict
            Raw user input features (12 features: 7 numerical + 5 categorical)
            
        Returns:
        --------
        dict
            Prediction result with:
            - 'health_risk_score': Predicted continuous score
            - 'risk_category': Categorized risk level
            - 'prediction_details': Dictionary with intermediate values
            
        Raises:
        -------
        ValueError
            If input validation fails
        RuntimeError
            If prediction pipeline fails
        """
        try:
            # STEP 1: Validate input
            print("\n" + "="*60)
            print("HEALTHCARE RISK PREDICTION - PHASE 3 PIPELINE")
            print("="*60 + "\n")
            
            print("STEP 1: Input Validation")
            print("-"*60)
            is_valid, error_msg = InputValidator.validate_input(input_dict)
            if not is_valid:
                raise ValueError(f"Input validation failed: {error_msg}")
            print("✓ Input validation passed")
            print(f"  - Age: {input_dict['Age']}")
            print(f"  - Category: {input_dict['Gender']}, {input_dict['Residence']}")
            
            # STEP 2: Preprocess features
            print("\nSTEP 2: Feature Preprocessing")
            print("-"*60)
            X_processed = FeatureProcessor.preprocess_input(input_dict, self.models['preprocessor'])
            print(f"✓ Features preprocessed: shape {X_processed.shape}")
            print(f"  - Numerical features scaled")
            print(f"  - Categorical features one-hot encoded")
            print(f"  - Result: 19 processed features")
            
            # STEP 3: Extract latent features
            print("\nSTEP 3: Latent Feature Extraction")
            print("-"*60)
            latent_features = FeatureProcessor.extract_latent_features(
                X_processed, self.models['encoder']
            )
            print(f"✓ Latent features extracted: shape {latent_features.shape}")
            print(f"  - 4-dimensional bottleneck representation")
            print(f"  - Captures abstract health patterns")
            
            # STEP 4: Create hybrid features
            print("\nSTEP 4: Hybrid Feature Creation")
            print("-"*60)
            hybrid_features = FeatureProcessor.create_hybrid_features(
                latent_features, X_processed
            )
            print(f"✓ Hybrid features created: shape {hybrid_features.shape}")
            print(f"  - Latent (4-dim) + Original (19-dim) = 23-dim")
            
            # STEP 5: Predict health risk score
            print("\nSTEP 5: Risk Score Prediction")
            print("-"*60)
            health_risk_score = self.models['ann_model'].predict(hybrid_features, verbose=0)[0, 0]
            print(f"✓ Health Risk Score predicted: {health_risk_score:.2f}")
            
            # STEP 6: Categorize risk
            print("\nSTEP 6: Risk Categorization")
            print("-"*60)
            risk_category = self._categorize_risk(health_risk_score)
            print(f"✓ Risk Category: {risk_category}")
            print(f"  - Low Risk: score < 35")
            print(f"  - Medium Risk: 35 ≤ score < 65")
            print(f"  - High Risk: score ≥ 65")
            
            # Prepare output
            prediction_result = {
                'health_risk_score': float(health_risk_score),
                'risk_category': risk_category,
                'prediction_details': {
                    'input_features': input_dict,
                    'latent_features': latent_features[0].tolist(),  # 4-dim
                    'model_metrics': self.models.get('metrics', {})
                }
            }
            
            print("\n" + "="*60)
            print("PREDICTION COMPLETE")
            print("="*60)
            
            return prediction_result
            
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {str(e)}")
    
    @staticmethod
    def _categorize_risk(score: float) -> str:
        """
        Categorize health risk score into risk levels.
        
        Parameters:
        -----------
        score : float
            Predicted health risk score
            
        Returns:
        --------
        str
            Risk category: "Low Risk", "Medium Risk", or "High Risk"
        """
        if score < RiskConfig.LOW_RISK_THRESHOLD:
            return "Low Risk"
        elif score < RiskConfig.MEDIUM_RISK_THRESHOLD:
            return "Medium Risk"
        else:
            return "High Risk"


# ============================================================
# MAIN - SAMPLE PREDICTION
# ============================================================

def main():
    """
    Demonstration with sample input using REALISTIC RAW DATASET VALUES.
    
    CRITICAL: Users input RAW values (original dataset ranges), not standardized values.
    The preprocessing pipeline automatically applies StandardScaler normalization.
    """
    
    # Sample user input - typical 45-year-old patient from dataset
    # All values are in ORIGINAL dataset ranges (RAW, not standardized)
    sample_input = {
        # Numerical features - ORIGINAL DATASET RANGES
        'Age': 45,                           # Range: 18-60
        'Health_Awareness_Score': 3,        # Range: 1-5 (1=low, 5=high awareness)
        'Symptom_Severity': 3,              # Range: 1-5 (1=mild, 5=severe)
        'Distance_to_Healthcare_km': 25,    # Range: 1-49 kilometers
        'Fear_of_Cost': 0,                  # Range: 0-1 (0=no fear, 1=high fear)
        'Fear_of_Hospital': 1,              # Range: 0-1 (0=no fear, 1=high fear)
        'Delay_in_Seeking_Care_Days': 60,   # Range: 0-119 days
        
        # Categorical features - EXACT DATASET VALUES
        'Gender': 'Male',
        'Residence': 'Urban',
        'Education_Level': 'High',           # Exact values: 'High', 'Low', or 'Medium'
        'Income_Level': 'Middle',            # Exact values: 'Low', 'Middle', or 'High'
        'Insurance_Status': 'Insured',
    }
    
    print("\n" + "="*60)
    print("SAMPLE INPUT DATA")
    print("="*60)
    for key, value in sample_input.items():
        print(f"  {key}: {value}")
    
    try:
        # Initialize predictor and make prediction
        predictor = RiskPredictor()
        result = predictor.predict_risk(sample_input)
        
        # Display result
        print("\n" + "="*60)
        print("PREDICTION RESULT")
        print("="*60)
        print(f"\nHealth Risk Score: {result['health_risk_score']:.2f}")
        print(f"Risk Category: {result['risk_category']}")
        
        # Optional: Show model metrics if available
        if result['prediction_details']['model_metrics']:
            print("\nModel Metrics (from training):")
            metrics = result['prediction_details']['model_metrics']
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value:.4f}")
        
        # Return result as JSON for potential API use
        print("\n" + "="*60)
        print("JSON OUTPUT (for API integration)")
        print("="*60)
        output_json = {
            'health_risk_score': result['health_risk_score'],
            'risk_category': result['risk_category']
        }
        print(json.dumps(output_json, indent=2))
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
