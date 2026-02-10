"""
Detailed OCR test script to show full extracted text using Ultimate OCR Service.
"""
import asyncio
import time
from services.ultimate_ocr_service import extract_text_from_path

async def test_ocr_detailed():
    print('🔍 DETAILED OCR TEST')
    print('=' * 50)
    
    # Test with a sample image (if available)
    try:
        result = await extract_text_from_path('uploads/test5.pdf')
        
        print(f'📁 File: uploads/test5.pdf')
        print(f'⏱️  Time: {time.time():.2f} seconds')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print()
        text_content = result.get("text", "")
        print(f'📝 Length: {len(text_content)} characters')
        print()
        
        # Show full extracted text
        extracted_text = result.get('text', '').strip()
        if extracted_text:
            print('📖 EXTRACTED TEXT:')
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
    result = asyncio.run(test_ocr_detailed())
