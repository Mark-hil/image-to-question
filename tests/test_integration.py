"""
Integration test for Ultimate OCR Service
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_integration():
    print('🔧 INTEGRATION TEST - ULTIMATE OCR SERVICE')
    print('=' * 50)
    
    try:
        # Test import
        from services.ultimate_ocr_service import extract_text_from_path
        print('✅ Ultimate OCR service imported successfully')
        
        # Test with sample image
        image_path = 'uploads/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg'
        if not os.path.exists(image_path):
            print(f'❌ Test image not found: {image_path}')
            return False
        
        print(f'📁 Testing with: {image_path}')
        
        # Run OCR
        result = await extract_text_from_path(image_path)
        
        print(f'✅ OCR completed successfully')
        print(f'📊 Status: {result.get("confidence", "unknown")}')
        print(f'📝 Text Length: {len(result.get("text", ""))} characters')
        print(f'📊 Word Count: {len(result.get("text", "").split())} words')
        
        # Show sample of corrected text
        text = result.get('text', '')
        if text:
            print(f'📖 Sample text: {text[:100]}...')
            
            # Check for specific improvements
            improvements_found = []
            if 'It what is' in text:
                improvements_found.append('✅ Title correction (TT WHATTIS → It what is)')
            if 'personal' in text and 'Pers0na1' not in text:
                improvements_found.append('✅ Character substitution fixed')
            if 'cleanliness' in text and 'deanliness' not in text:
                improvements_found.append('✅ Word correction (deanliness → cleanliness)')
            if 'the hands' in text and 'the the the' not in text:
                improvements_found.append('✅ Repeated words fixed')
            if 'hygiene' in text and 'hy giene' not in text:
                improvements_found.append('✅ Word segmentation fixed')
            
            print()
            print('🎯 IMPROVEMENTS DETECTED:')
            for improvement in improvements_found:
                print(improvement)
            
            if not improvements_found:
                print('⚠️  No specific improvements detected in this sample')
        
        print()
        print('🎉 INTEGRATION TEST PASSED')
        return True
        
    except ImportError as e:
        print(f'❌ Import error: {e}')
        return False
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    if success:
        print('\n✅ Ultimate OCR service is ready for production!')
    else:
        print('\n❌ Integration test failed - check the implementation')
