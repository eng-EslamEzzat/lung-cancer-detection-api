"""
API endpoints for the lung cancer detection service
"""

import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.prediction import PredictionResponse, HealthResponse, ErrorResponse
from app.services.image_processor import image_processor

logger = get_logger(__name__)

# Create router
router = APIRouter()

# Track service start time
service_start_time = time.time()


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION,
        "docs_url": "/docs"
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        current_time = datetime.utcnow()
        uptime = time.time() - service_start_time
        
        # Get image processor health status
        processor_health = image_processor.get_health_status()
        
        return HealthResponse(
            status="healthy",
            service=settings.APP_NAME,
            version=settings.APP_VERSION,
            timestamp=current_time.isoformat(),
            uptime_seconds=uptime,
            model_loaded=processor_health.get("model_loaded", False)
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@router.post("/predict", response_model=PredictionResponse)
async def predict_image(file: UploadFile = File(...)):
    """
    Predict lung cancer from uploaded medical image
    
    Args:
        file: Uploaded image file (JPEG, PNG, TIFF, BMP)
        
    Returns:
        Prediction results with confidence scores and image analysis
        
    Raises:
        HTTPException: For various error conditions
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine file type"
        )
    
    logger.info(f"Processing image: {file.filename} ({file.content_type})")
    
    try:
        # Read file data
        image_data = await file.read()
        
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file provided"
            )
        
        # Process image
        result = image_processor.process_image(
            image_data=image_data,
            filename=file.filename,
            content_type=file.content_type
        )
        
        logger.info(f"Successfully processed {file.filename}")
        
        return PredictionResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid image file {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
        
    except RuntimeError as e:
        logger.error(f"Model error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model service unavailable: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during image processing"
        )


@router.get("/model/info")
async def get_model_info():
    """Get information about the loaded model"""
    try:
        health_status = image_processor.get_health_status()
        
        return {
            "model_loaded": health_status["model_loaded"],
            "supported_formats": health_status["supported_formats"],
            "max_file_size_mb": health_status["max_file_size_mb"],
            "model_input_size": health_status["model_input_size"],
            "confidence_threshold": settings.CONFIDENCE_THRESHOLD
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving model information"
        )