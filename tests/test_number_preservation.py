"""
Test to verify numbers are preserved in Ultimate OCR Service
"""
import asyncio
from services.ultimate_ocr_service import UltimateOCRService

async def test_number_preservation():
    print('🔢 TESTING NUMBER PRESERVATION')
    print('=' * 50)
    
    service = UltimateOCRService()
    
    # Test text with various numbers
    test_text = "Recipe 2: Mix 1 cup of flour with 2 eggs and 8 tablespoons of sugar. Cook for 5 minutes at 350 degrees."
    
    print(f'📝 Original text: "{test_text}"')
    print()
    
    # Apply character corrections
    step1 = service.fix_character_substitutions(test_text)
    print(f'🔧 After character corrections: "{step1}"')
    
    # Apply severe distortions
    step2 = service.fix_severe_distortions(step1)
    print(f'🔧 After severe distortions: "{step2}"')
    
    # Check if numbers are preserved
    numbers_in_original = ['2', '1', '2', '8', '5', '350']
    numbers_in_result = []
    
    import re
    for num in numbers_in_original:
        if re.search(r'\b' + num + r'\b', step2):
            numbers_in_result.append(num)
    
    print()
    print('📊 NUMBER PRESERVATION CHECK:')
    print(f'✅ Original numbers: {numbers_in_original}')
    print(f'✅ Preserved numbers: {numbers_in_result}')
    print(f'✅ All numbers preserved: {len(numbers_in_result) == len(numbers_in_original)}')
    
    if len(numbers_in_result) == len(numbers_in_original):
        print('🎉 SUCCESS: All numbers are preserved correctly!')
    else:
        print('❌ ISSUE: Some numbers were changed!')
    
    return step2

if __name__ == "__main__":
    result = asyncio.run(test_number_preservation())
