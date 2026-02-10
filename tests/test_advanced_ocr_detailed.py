"""
Detailed Advanced OCR test script to show full extracted text with improvements.
"""
import asyncio
import time
from advanced_ocr_service import extract_text_from_path

async def test_advanced_ocr_detailed():
    print('🚀 ADVANCED DETAILED OCR TEST')
    print('=' * 50)
    
    # Test with a sample image (if available)
    try:
        start_time = time.time()
        result = await extract_text_from_path('uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg')
        end_time = time.time()
        
        print(f'📁 File: uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg')
        print(f'⏱️  Time: {end_time - start_time:.2f} seconds')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print()
        text_content = result.get("text", "")
        print(f'📝 Length: {len(text_content)} characters')
        print()
        
        # Show full extracted text
        extracted_text = result.get('text', '').strip()
        if extracted_text:
            print('📖 ADVANCED EXTRACTED TEXT:')
            print('-' * 30)
            print(extracted_text)
            print('-' * 30)
        else:
            print('❌ No text extracted')
        
        print('=' * 50)
        
        # Show word count and first few words
        if extracted_text:
            words = extracted_text.split()
            print(f'📊 Word Count: {len(words)} words')
            print(f'🔤 First 10 words: {words[:10]}')
        
        return result
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return None

if __name__ == "__main__":
    result = asyncio.run(test_advanced_ocr_detailed())
