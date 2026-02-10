"""
Test title and content separation in Ultimate OCR Service
"""
import asyncio
import time
from services.ultimate_ocr_service import extract_text_from_path

async def test_title_separation():
    print('📖 TITLE SEPARATION TEST')
    print('=' * 50)
    
    try:
        start_time = time.time()
        result = await extract_text_from_path('uploads/test1.png')
        end_time = time.time()
        
        print(f'⏱️  Processing Time: {end_time - start_time:.2f} seconds')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print()
        
        # Show the formatted text with clear separation
        corrected_text = result.get('text', '').strip()
        print('📖 FORMATTED TEXT WITH TITLE/CONTENT SEPARATION:')
        print('=' * 60)
        
        # Split by double newlines to show title vs content
        sections = corrected_text.split('\n\n')
        
        for i, section in enumerate(sections):
            if section.strip():
                if i == 0 and len(sections) > 1:
                    print('📝 TITLE:')
                    print(f'   "{section.strip()}"')
                elif i == 1:
                    print('\n📄 CONTENT:')
                    print(f'   "{section.strip()}"')
                else:
                    print(f'\n📑 SECTION {i+1}:')
                    print(f'   "{section.strip()}"')
        
        print('=' * 60)
        print()
        
        # Analyze the separation
        if len(sections) > 1:
            title = sections[0].strip()
            content = sections[1].strip()
            
            print('🎯 TITLE/CONTENT ANALYSIS:')
            print(f'📝 Title length: {len(title.split())} words')
            print(f'📄 Content length: {len(content.split())} words')
            print(f'📏 Total length: {len(corrected_text)} characters')
            print()
            
            # Check if title contains title keywords
            title_keywords = ['models', 'api', 'service', 'features', 'supported']
            content_indicators = ['supports', 'provides', 'offers', 'enables', 'allows']
            
            title_has_keywords = any(keyword in title.lower() for keyword in title_keywords)
            content_has_indicators = any(indicator in content.lower() for indicator in content_indicators)
            
            print('🔍 STRUCTURE VALIDATION:')
            if title_has_keywords:
                print('✅ Title contains title keywords')
            else:
                print('❌ Title missing title keywords')
            
            if content_has_indicators:
                print('✅ Content contains descriptive indicators')
            else:
                print('❌ Content missing descriptive indicators')
            
            if len(title.split()) <= 6:
                print('✅ Title is appropriately short')
            else:
                print('⚠️  Title might be too long')
            
            if len(content.split()) > len(title.split()):
                print('✅ Content is longer than title')
            else:
                print('⚠️  Content should be longer than title')
        
        else:
            print('⚠️  No title/content separation detected')
            print('📝 Single section text:')
            print(f'   "{sections[0].strip()}"')
        
        return result
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    result = asyncio.run(test_title_separation())
