"""
Simple test for OCR service
"""
import asyncio
import time
from simple_ocr_service import extract_text_from_path

async def test_simple():
    print('🧹 TESTING SIMPLE OCR SERVICE')
    print('=' * 30)
    
    start = time.time()
    
    try:
        result = await extract_text_from_path('uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg')
        end = time.time()
        
        print(f'✅ Time: {end - start:.2f} seconds')
        print(f'📝 Text: {str(result.get("text", ""))[:100]}...')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        
        return result
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    result = asyncio.run(test_simple())
