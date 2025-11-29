# test.py
import os
import asyncio
from services.vision_service import describe_image_stub

async def test_vision(image_path: str):
    """Test the vision service with an image file."""
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {os.path.abspath(image_path)}")
        return
    
    print(f"\nTesting vision on: {os.path.abspath(image_path)}")
    
    try:
        # Get image description using Groq API (includes OCR text)
        description = await describe_image_stub(image_path)
        
        # Print results (contains EXTRACTED TEXT then DESCRIPTION)
        print("\n" + "="*50)
        print("RESULT:")
        print("="*50)
        print(description)
        print("="*50)
        
    except Exception as e:
        print(f"\nError during processing: {str(e)}")

if __name__ == "__main__":
    # Specify the path to your image
    image_path = "uploads/testb2.jpeg"
    
    
    # Run the async test
    asyncio.run(test_vision(image_path))