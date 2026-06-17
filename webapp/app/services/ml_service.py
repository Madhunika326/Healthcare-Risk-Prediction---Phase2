"""
ML Prediction Service
Wraps the trained ML models and prediction pipeline
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Any

# Add parent directory to path to import predict_risk
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from predict_risk import (
        RiskConfig, ModelLoader, InputValidator,
        FeatureProcessor, RiskPredictor
    )
except ImportError as e:
    print(f"Warning: Could not import prediction pipeline: {e}")


class MLPredictionService:
    """Service class for making healthcare risk predictions"""
    
    def __init__(self, models_path=None):
        """
        Initialize the prediction service
        
        Args:
            models_path: Path to models directory
        """
        self.models_path = models_path or Path(__file__).parent.parent.parent / 'models'
        self.predictor = None
        self.config = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize and load ML models"""
        try:
            # Initialize predictor
            self.config = RiskConfig(str(self.models_path))
            self.predictor = RiskPredictor(self.config)
            print("ML models loaded successfully")
        except Exception as e:
            print(f"Error initializing ML models: {e}")
            raise
    
    def validate_input(self, input_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate input data
        
        Args:
            input_data: Dictionary with input features
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            InputValidator.validate_input(input_data)
            return True, "Valid input"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction
        
        Args:
            input_data: Dictionary with input features
        
        Returns:
            Dictionary with prediction results
        """
        try:
            # Validate input
            is_valid, error_msg = self.validate_input(input_data)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg,
                    'health_risk_score': None,
                    'risk_category': None
                }
            
            # Make prediction
            result = self.predictor.predict_risk(input_data)
            
            return {
                'success': True,
                'health_risk_score': round(float(result['health_risk_score']), 2),
                'risk_category': result['risk_category'],
                'risk_factors': self._extract_risk_factors(input_data, result['health_risk_score']),
                'recommendations': self._generate_recommendations(input_data, result['risk_category']),
                'confidence': self._estimate_confidence(result['health_risk_score'])
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Prediction error: {str(e)}",
                'health_risk_score': None,
                'risk_category': None
            }
    
    def batch_predict(self, input_list: list) -> list:
        """
        Make multiple predictions
        
        Args:
            input_list: List of input dictionaries
        
        Returns:
            List of prediction results
        """
        results = []
        for input_data in input_list:
            results.append(self.predict(input_data))
        return results
    
    def _extract_risk_factors(self, input_data: Dict, risk_score: float) -> list:
        """Extract key risk factors from input"""
        factors = []
        
        # Age risk
        if input_data.get('Age', 0) > 50:
            factors.append({
                'factor': 'Age',
                'value': input_data.get('Age'),
                'severity': 'High',
                'description': 'Age above 50 increases health risk'
            })
        
        # Symptom severity risk
        if input_data.get('Symptom_Severity', 0) > 3:
            factors.append({
                'factor': 'Symptom Severity',
                'value': input_data.get('Symptom_Severity'),
                'severity': 'High',
                'description': 'High symptom severity detected'
            })
        
        # Delay in seeking care
        if input_data.get('Delay_in_Seeking_Care_Days', 0) > 60:
            factors.append({
                'factor': 'Delay in Care',
                'value': input_data.get('Delay_in_Seeking_Care_Days'),
                'severity': 'High',
                'description': f'Significant delay of {int(input_data.get("Delay_in_Seeking_Care_Days", 0))} days'
            })
        
        # Distance to healthcare
        if input_data.get('Distance_to_Healthcare_km', 0) > 30:
            factors.append({
                'factor': 'Distance to Healthcare',
                'value': input_data.get('Distance_to_Healthcare_km'),
                'severity': 'Medium',
                'description': f'Healthcare facility {input_data.get("Distance_to_Healthcare_km", 0):.1f}km away'
            })
        
        # Healthcare barriers
        fear_cost = input_data.get('Fear_of_Cost', 0)
        fear_hospital = input_data.get('Fear_of_Hospital', 0)
        if fear_cost > 0.7 or fear_hospital > 0.7:
            factors.append({
                'factor': 'Healthcare Barriers',
                'value': max(fear_cost, fear_hospital),
                'severity': 'Medium',
                'description': 'Financial or psychological barriers to healthcare'
            })
        
        # Low health awareness
        if input_data.get('Health_Awareness_Score', 0) < 2:
            factors.append({
                'factor': 'Health Awareness',
                'value': input_data.get('Health_Awareness_Score'),
                'severity': 'Medium',
                'description': 'Low health awareness may impact preventive care'
            })
        
        return factors
    
    def _generate_recommendations(self, input_data: Dict, risk_category: str) -> list:
        """Generate personalized health recommendations"""
        recommendations = []
        
        if input_data.get('Symptom_Severity', 0) > 3:
            recommendations.append('Seek immediate medical consultation for symptom evaluation')
        
        if input_data.get('Delay_in_Seeking_Care_Days', 0) > 30:
            recommendations.append('Establish a regular healthcare monitoring schedule')
        
        if input_data.get('Distance_to_Healthcare_km', 0) > 25:
            recommendations.append('Consider telehealth services for remote consultations')
        
        if input_data.get('Fear_of_Cost', 0) > 0.5:
            recommendations.append('Explore healthcare insurance options and subsidized services')
        
        if input_data.get('Health_Awareness_Score', 0) < 2:
            recommendations.append('Participate in health education programs')
        
        if risk_category == 'High':
            recommendations.append('Schedule comprehensive health assessment with provider')
            recommendations.append('Implement preventive care measures immediately')
        
        if risk_category == 'Medium':
            recommendations.append('Monitor health parameters regularly')
            recommendations.append('Maintain preventive healthcare appointments')
        
        return recommendations
    
    def _estimate_confidence(self, risk_score: float) -> str:
        """Estimate confidence level based on risk score"""
        if risk_score < 30 or risk_score > 70:
            return 'High'
        elif risk_score < 40 or risk_score > 60:
            return 'Medium'
        else:
            return 'Medium-Low'
    
    def get_population_statistics(self) -> Dict[str, Any]:
        """Get population-level statistics"""
        return {
            'average_risk_score': 44.5,
            'low_risk_percentage': 35,
            'medium_risk_percentage': 50,
            'high_risk_percentage': 15,
            'total_assessments': 3836,
            'age_range': '18-60 years'
        }


# Global service instance
_ml_service = None


def get_ml_service(models_path=None):
    """Get or create ML service instance"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLPredictionService(models_path)
    return _ml_service
