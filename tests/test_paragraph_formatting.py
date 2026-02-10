"""
Test paragraph and title formatting in Ultimate OCR Service
"""
import asyncio
import time
from services.ultimate_ocr_service import extract_text_from_path

async def test_paragraph_formatting():
    print('📝 PARAGRAPH FORMATTING TEST')
    print('=' * 50)
    
    try:
        start_time = time.time()
        result = await extract_text_from_path('uploads/test1.png')
        end_time = time.time()
        
        print(f'⏱️  Processing Time: {end_time - start_time:.2f} seconds')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print(f'📝 Text Length: {len(result.get("text", ""))} characters')
        print()
        
        # Show the formatted text with line breaks visible
        corrected_text = result.get('text', '').strip()
        print('📖 FORMATTED TEXT (with line breaks):')
        print('-' * 50)
        # Show line breaks as visible markers
        display_text = corrected_text.replace('\n', '↵\n').replace('  ', '··')
        print(display_text)
        print('-' * 50)
        print()
        
        # Show the actual formatted text
        print('📖 ACTUAL FORMATTED TEXT:')
        print('-' * 50)
        print(corrected_text)
        print('-' * 50)
        print()
        
        # Analyze formatting
        lines = corrected_text.split('\n')
        paragraphs = [p.strip() for p in lines if p.strip()]
        
        print('📊 FORMATTING ANALYSIS:')
        print(f'📝 Total lines: {len(lines)}')
        print(f'📄 Paragraphs: {len(paragraphs)}')
        print(f'📏 Average paragraph length: {sum(len(p) for p in paragraphs) / len(paragraphs):.1f} chars')
        
        # Check for specific improvements
        improvements = []
        
        if len(paragraphs) > 1:
            improvements.append('✅ Multiple paragraphs detected')
        
        if '(' in corrected_text and ')' in corrected_text:
            improvements.append('✅ Parentheses preserved')
        
        if 'OCR' in corrected_text:
            improvements.append('✅ Acronyms preserved')
        
        if any(line.strip().endswith('.') for line in lines):
            improvements.append('✅ Proper sentence endings')
        
        print()
        print('🎯 FORMATTING IMPROVEMENTS:')
        for improvement in improvements:
            print(improvement)
        
        return result
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    result = asyncio.run(test_paragraph_formatting())
