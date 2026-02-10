"""
Test the full OCR pipeline to see where newlines are being lost
"""
import asyncio
import re
from services.ultimate_ocr_service import UltimateOCRService

async def test_full_pipeline():
    print('🔍 FULL OCR PIPELINE DEBUG')
    print('=' * 50)
    
    # Test text
    test_text = "Supported models grog api supports powerful multimodal models that can be easily integrated into your applications to provide fast and accurate image processing for tasks such as visual question answering, caption generation, and optical character recognition (ocr)."
    
    print(f'📝 Original text: "{test_text}"')
    print()
    
    # Create service instance
    service = UltimateOCRService()
    
    # Test each step individually
    print('🔍 STEP 1: Character substitutions')
    step1 = service.fix_character_substitutions(test_text)
    print(f'   Result: "{step1}"')
    print()
    
    print('🔍 STEP 2: Severe distortions')
    step2 = service.fix_severe_distortions(step1)
    print(f'   Result: "{step2}"')
    print()
    
    print('🔍 STEP 3: Repeated words')
    step3 = service.fix_repeated_words(step2)
    print(f'   Result: "{step3}"')
    print()
    
    print('🔍 STEP 4: Broken/merged words')
    step4 = service.fix_broken_merged_words(step3)
    print(f'   Result: "{step4}"')
    print()
    
    print('🔍 STEP 5: Verb tenses')
    step5 = service.fix_verb_tenses(step4)
    print(f'   Result: "{step5}"')
    print()
    
    print('🔍 STEP 6: Clean punctuation')
    step6 = service.clean_punctuation_symbols(step5)
    print(f'   Result: "{step6}"')
    print()
    
    print('🔍 STEP 7: Format titles and paragraphs')
    step7 = service.format_titles_and_paragraphs(step6)
    print(f'   Result: "{step7}"')
    newline_check = "\n\n" in step7
    print(f'   Contains newlines: {newline_check}')
    print()
    
    print('🔍 STEP 8: Fix capitalization')
    step8 = service.fix_capitalization(step7)
    print(f'   Result: "{step8}"')
    newline_check = "\n\n" in step8
    print(f'   Contains newlines: {newline_check}')
    print()
    
    print('🔍 STEP 9: Fix OCR grammar')
    step9 = service.fix_ocr_grammar(step8)
    print(f'   Result: "{step9}"')
    newline_check = "\n\n" in step9
    print(f'   Contains newlines: {newline_check}')
    print()
    
    print('🔍 STEP 10: Final cleanup')
    print(f'   Input to final cleanup: "{step9}"')
    step10 = service.final_cleanup(step9)
    print(f'   Result: "{step10}"')
    newline_check = "\n\n" in step10
    print(f'   Contains newlines: {newline_check}')
    
    # Debug the final cleanup step by step
    print('🔍 DEBUGGING FINAL CLEANUP:')
    debug_text = step9
    print(f'   Start: "{debug_text}"')
    
    # Step 1: Remove symbols
    debug_text = re.sub(r'[^a-zA-Z0-9\s.,!?;:\-\'"()\n]', '', debug_text)
    print(f'   After symbol removal: "{debug_text}"')
    
    # Step 2: Split lines
    lines = debug_text.split('\n')
    print(f'   Lines: {lines}')
    
    # Step 3: Clean each line
    cleaned_lines = []
    for line in lines:
        line = re.sub(r'[ \t]+', ' ', line)
        line = line.strip()
        cleaned_lines.append(line)
        print(f'   Cleaned line: "{line}"')
    
    # Step 4: Rejoin
    debug_text = '\n'.join(cleaned_lines)
    print(f'   After rejoin: "{debug_text}"')
    
    # Step 5: Fix parentheses spacing
    debug_text = re.sub(r'\s*\(\s*', ' (', debug_text)
    debug_text = re.sub(r'\s*\)\s*', ') ', debug_text)
    debug_text = re.sub(r'\)\s+([a-z])', r') \1', debug_text)
    print(f'   After parentheses fix: "{debug_text}"')
    
    # Step 6: Fix punctuation spacing
    debug_text = re.sub(r'([.,!?;:])\s*([a-zA-Z])', r'\1 \2', debug_text)
    print(f'   After punctuation fix: "{debug_text}"')
    
    # Step 7: Add final period
    if debug_text and not debug_text[-1] in '.!?':
        debug_text += '.'
    print(f'   Final result: "{debug_text}"')
    print()
    
    print('🎯 FINAL RESULT:')
    print('=' * 30)
    print(step10)
    print('=' * 30)
    
    # Show with visible newlines
    print('📖 WITH VISIBLE NEWLINES:')
    print('=' * 30)
    visible = step10.replace('\n', '↵\n')
    print(visible)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
