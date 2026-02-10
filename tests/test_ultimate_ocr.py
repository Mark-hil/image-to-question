"""
Test the Ultimate OCR service with severe error correction
"""
import asyncio
import time
from services.ultimate_ocr_service import extract_text_from_path
from ocr_error_analyzer import analyze_ocr_text

async def test_ultimate_ocr():
    print('🏆 TESTING ULTIMATE OCR SERVICE')
    print('=' * 50)
    
    try:
        start_time = time.time()
        result = await extract_text_from_path('uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg')
        end_time = time.time()
        
        print(f'⏱️  Processing Time: {end_time - start_time:.2f} seconds')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print(f'📝 Text Length: {len(result.get("text", ""))} characters')
        print()
        
        # Show the ultimate corrected text
        corrected_text = result.get('text', '').strip()
        print('🏆 ULTIMATE CORRECTED TEXT:')
        print('-' * 40)
        print(corrected_text)
        print('-' * 40)
        print()
        
        # Analyze the corrected text for remaining errors
        print('🔍 ERROR ANALYSIS OF ULTIMATE CORRECTED TEXT:')
        print('=' * 40)
        error_report = analyze_ocr_text(corrected_text)
        print(error_report)
        
        # Show word analysis
        words = corrected_text.split()
        print(f'📊 Word Count: {len(words)} words')
        print(f'🔤 First 15 words: {words[:15]}')
        
        return result
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    result = asyncio.run(test_ultimate_ocr())
