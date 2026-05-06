import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.file_parser import parse_file
from app.services.code_runner import run_code
from app.services.nlp_evaluator import evaluate_similarity, evaluate_grammar
from app.services.plagiarism import check_plagiarism
from app.services.rubric_grader import apply_rubric

def test_file_parser():
    print("\n--- Testing File Parser ---")
    # Non-existent file
    print(f"Non-existent: {parse_file('no_such_file.pdf')}")
    # Empty file path
    try:
        print(f"Empty path: {parse_file('')}")
    except Exception as e:
        print(f"Empty path error: {e}")

def test_code_runner():
    print("\n--- Testing Code Runner ---")
    # Syntax error
    res = run_code('python', 'print("hello"', [{'input': '', 'expected_output': 'hello'}])
    print(f"Syntax Error Results: {res['results'][0]['error']}")
    
    # Infinite loop
    print("Testing infinite loop (wait 10s)...")
    res = run_code('python', 'while True: pass', [{'input': '', 'expected_output': 'done'}])
    print(f"Infinite Loop Results: {res['results'][0]['error']}")

def test_nlp():
    print("\n--- Testing NLP ---")
    # Empty strings
    print(f"Similarity (empty): {evaluate_similarity('', '')}")
    # Single word
    print(f"Grammar (short): {evaluate_grammar('hello')}")

def test_plagiarism():
    print("\n--- Testing Plagiarism ---")
    # Huge text (simulated)
    huge_text = "word " * 60000
    res = check_plagiarism(huge_text, [{'text': 'word ' * 1000}])
    print(f"Huge text handled: {len(res['disclaimer']) > 0}")

if __name__ == '__main__':
    # Create a dummy file for parser test
    with open('dummy.txt', 'w') as f: f.write('test')
    
    test_file_parser()
    test_code_runner()
    test_nlp()
    test_plagiarism()
    
    # Cleanup
    if os.path.exists('dummy.txt'): os.remove('dummy.txt')
