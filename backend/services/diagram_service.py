import datetime
import os
import torch
from diffusers import StableDiffusionPipeline
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DiagramService:
    def __init__(self, model_path="./models/sd-ai2d-model"):
        """Initialize the diagram generation service"""
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Load the model"""
        try:
            logger.info(f"Loading diagram model from {self.model_path}...")
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                safety_checker=None,
            ).to(self.device)
            logger.info("Diagram model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading diagram model: {str(e)}")
            raise
    
    def generate_diagram(
        self,
        prompt,
        num_inference_steps=5,
        guidance_scale=7.5,
        output_dir="./generated"
    ):
        """Generate a single diagram"""
        try:
            if not self.pipeline:
                raise ValueError("Model not initialized")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate image
            logger.info(f"Generating diagram for prompt: {prompt}")
            image = self.pipeline(
                prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
            ).images[0]
            
            # Save image with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagram_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            image.save(filepath)
            
            logger.info(f"Diagram saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            raise