"""
Image processing service for lung cancer detection
"""

import time
from typing import Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image
import io
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.prediction import ImageInfo, ImageStats, PredictionResult

logger = get_logger(__name__)


class ImageProcessor:
    """Image processing and prediction service"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self):
        """Load the machine learning model"""
        try:
            import keras
            
            # Load the model using tensorflow.keras
            model_path = settings.get_model_path()
            self.model = keras.models.load_model(model_path)
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model_loaded = False
    
    def validate_image(self, content_type: str, file_size: int) -> bool:
        """Validate uploaded image"""
        if not content_type or content_type not in settings.get_allowed_image_types():
            return False
        
        if file_size > settings.MAX_FILE_SIZE:
            return False
        
        return True
    
    def extract_image_info(self, image: Image.Image, file_size: Optional[int] = None) -> ImageInfo:
        """Extract basic image information"""
        width, height = image.size
        channels = len(image.getbands()) if image.getbands() else 0
        format_name = image.format
        
        return ImageInfo(
            width=width,
            height=height,
            channels=channels,
            format=format_name
        )
    
    def calculate_image_stats(self, image_array: np.ndarray, file_size: Optional[int] = None) -> ImageStats:
        """Calculate image statistics"""
        mean_intensity = float(np.mean(image_array))
        std_intensity = float(np.std(image_array))
        shape = list(image_array.shape)
        
        return ImageStats(
            mean_intensity=mean_intensity,
            std_intensity=std_intensity,
            shape=shape,
            size_bytes=file_size
        )
    
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for model prediction"""
        # Convert from RGB to B&W if necessary
        if image.mode != 'L':
            image = image.convert('L')
        
        # Resize to model input size
        target_size = settings.get_model_input_size()
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        image_array = np.array(image, dtype=np.float32)
        
        # Normalize pixel values (0-1)
        image_array = image_array / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    
    def predict(self, preprocessed_image: np.ndarray) -> Dict[str, Any]:
        """Make prediction using the loaded model"""
        start_time = time.time()
        
        try:
            if not self.model_loaded:
                raise RuntimeError("Model not loaded")

            # Get model predictions (softmax probabilities)
            predictions = self.model.predict(preprocessed_image)
            
            # Extract probabilities for each class
            class_probs = predictions[0]  # Get probabilities for the single image
            
            # Get the predicted class index (highest probability)
            predicted_class_idx = np.argmax(class_probs)
            
            # Get confidence (highest probability value)
            confidence = float(np.max(class_probs))
            
            # Map the predicted class index to the corresponding label
            class_labels = ["Benign Case", "Malignant Case", "Normal Case"]
            prediction_class = class_labels[predicted_class_idx]
            
            # Create probabilities dictionary
            probabilities = {
                "Benign Case": float(class_probs[0]),
                "Malignant Case": float(class_probs[1]),
                "Normal Case": float(class_probs[2])
            }
            
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return {
                "prediction": prediction_class,
                "confidence": confidence,
                "probabilities": probabilities,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise
    
    def process_image(self, image_data: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Complete image processing pipeline"""
        file_size = len(image_data)
        
        # Validate image
        if not self.validate_image(content_type, file_size):
            raise ValueError("Invalid image file")
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Extract image info
            image_info = self.extract_image_info(image, file_size)
            
            # Convert to numpy array for stats
            image_array = np.array(image)
            image_stats = self.calculate_image_stats(image_array, file_size)
            
            # Preprocess for prediction
            preprocessed_image = self.preprocess_image(image)
            
            # Make prediction
            prediction_results = self.predict(preprocessed_image)
            
            # Create prediction result
            prediction_result = PredictionResult(**prediction_results)
            
            return {
                "status": "success",
                "filename": filename,
                "image_info": image_info,
                "image_stats": image_stats,
                "prediction_result": prediction_result,
                "message": "Image processed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the image processor"""
        return {
            "model_loaded": self.model_loaded,
            "supported_formats": settings.get_allowed_image_types(),
            "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
            "model_input_size": settings.get_model_input_size()
        }


# Global instance
image_processor = ImageProcessor()