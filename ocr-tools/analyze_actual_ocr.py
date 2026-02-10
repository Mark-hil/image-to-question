"""
Analyze the actual OCR text from your image
"""
import asyncio
from simple_ocr_service import extract_text_from_path
from ocr_error_analyzer import analyze_ocr_text

async def analyze_actual_ocr():
    print('🔍 DETAILED OCR ERROR ANALYSIS')
    print('=' * 60)
    
    try:
        # Get the actual OCR text
        result = await extract_text_from_path('uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg')
        ocr_text = result.get('text', '')
        
        print(f'📊 OCR TEXT LENGTH: {len(ocr_text)} characters')
        print(f'📊 WORD COUNT: {len(ocr_text.split())} words')
        print()
        
        # Show a preview of the OCR text
        print('📝 OCR TEXT PREVIEW:')
        print('-' * 40)
        preview = ocr_text[:500] + '...' if len(ocr_text) > 500 else ocr_text
        print(preview)
        print('-' * 40)
        print()
        
        # Analyze errors
        print('🔍 ERROR ANALYSIS:')
        print('=' * 40)
        error_report = analyze_ocr_text(ocr_text)
        print(error_report)
        
        return ocr_text
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    result = asyncio.run(analyze_actual_ocr())
