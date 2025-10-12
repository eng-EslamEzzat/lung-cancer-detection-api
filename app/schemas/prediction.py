"""
Pydantic schemas for prediction endpoints
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ImageInfo(BaseModel):
    """Image information schema"""
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    channels: Optional[int] = Field(None, description="Number of color channels")
    format: Optional[str] = Field(None, description="Image format (JPEG, PNG, etc.)")


class ImageStats(BaseModel):
    """Image statistics schema"""
    mean_intensity: float = Field(..., description="Mean pixel intensity")
    std_intensity: float = Field(..., description="Standard deviation of pixel intensity")
    shape: List[int] = Field(..., description="Image shape as [height, width, channels]")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")


class PredictionResult(BaseModel):
    """Prediction result schema"""
    prediction: str = Field(..., description="Prediction class (e.g., 'Normal', 'Suspicious', 'Malignant')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    probabilities: Optional[Dict[str, float]] = Field(None, description="Class probabilities")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class PredictionResponse(BaseModel):
    """Complete prediction response schema"""
    status: str = Field(..., description="Response status")
    filename: str = Field(..., description="Original filename")
    image_info: ImageInfo = Field(..., description="Image information")
    image_stats: Optional[ImageStats] = Field(None, description="Image statistics")
    prediction_result: PredictionResult = Field(..., description="Prediction results")
    message: str = Field(..., description="Response message")
    timestamp: Optional[str] = Field(None, description="Processing timestamp")


class ErrorResponse(BaseModel):
    """Error response schema"""
    status: str = Field(default="error", description="Response status")
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: Optional[str] = Field(None, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    model_loaded: Optional[bool] = Field(None, description="Whether the ML model is loaded")