"""
Compare OCR text cleaning results
"""
import asyncio
import time
from simple_ocr_service import extract_text_from_path

async def test_ocr_comparison():
    print('🔍 OCR TEXT CLEANING COMPARISON')
    print('=' * 50)
    
    try:
        result = await extract_text_from_path('uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg')
        
        print(f'⏱️  Processing Time: {time.time():.2f} seconds')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print(f'📝 Text Length: {len(result.get("text", ""))} characters')
        print()
        
        # Show the cleaned text
        cleaned_text = result.get('text', '').strip()
        print('🧹 CLEANED TEXT (Full):')
        print('-' * 40)
        print(cleaned_text)
        print('-' * 40)
        print()
        
        # Show word analysis
        words = cleaned_text.split()
        print(f'📊 Word Count: {len(words)} words')
        print(f'🔤 First 15 words: {words[:15]}')
        print()
        
        # Show character analysis
        char_count = len(cleaned_text)
        print(f'📊 Character Count: {char_count} characters')
        print(f'📊 Average Word Length: {char_count/len(words):.1f} characters per word')
        
        return result
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    result = asyncio.run(test_ocr_comparison())
