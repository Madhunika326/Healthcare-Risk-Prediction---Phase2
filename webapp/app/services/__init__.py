"""
Services module initialization
"""

from app.services.ml_service import MLPredictionService, get_ml_service

__all__ = ['MLPredictionService', 'get_ml_service']
