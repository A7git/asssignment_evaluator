"""Code runner service — executes student code in a sandboxed subprocess."""
import os
import subprocess
import tempfile
import json


def run_code(language, code_string, test_cases, timeout=10):
    """Execute student code against test cases.

    Args:
        language: Programming language ('python', 'java', 'cpp')
        code_string: The source code as a string.
        test_cases: List of dicts with 'input' and 'expected_output' keys.
        timeout: Maximum execution time in seconds.

    Returns:
        dict: {
            'passed': int,
            'total': int,
            'results': [{'input': str, 'expected': str, 'actual': str, 'passed': bool, 'error': str}],
            'compile_error': str or None
        }
    """
    if not test_cases:
        return {
            'passed': 0,
            'total': 0,
            'results': [],
            'compile_error': None,
            'message': 'No test cases defined for this assignment.'
        }

    runners = {
        'python': _run_python,
        'java': _run_java,
        'cpp': _run_cpp,
    }

    runner = runners.get(language)
    if not runner:
        return {
            'passed': 0,
            'total': len(test_cases),
            'results': [],
            'compile_error': f'Unsupported language: {language}'
        }

    results = []
    passed = 0

    for i, tc in enumerate(test_cases):
        tc_input = tc.get('input', '')
        tc_expected = tc.get('expected_output', '').strip()

        try:
            actual, error = runner(code_string, tc_input, timeout)
            actual = actual.strip() if actual else ''

            is_passed = actual == tc_expected
            if is_passed:
                passed += 1

            results.append({
                'test_num': i + 1,
                'input': tc_input,
                'expected': tc_expected,
                'actual': actual,
                'passed': is_passed,
                'error': error
            })
        except subprocess.TimeoutExpired:
            results.append({
                'test_num': i + 1,
                'input': tc_input,
                'expected': tc_expected,
                'actual': '',
                'passed': False,
                'error': f'Time limit exceeded ({timeout}s)'
            })
        except Exception as e:
            results.append({
                'test_num': i + 1,
                'input': tc_input,
                'expected': tc_expected,
                'actual': '',
                'passed': False,
                'error': str(e)
            })

    return {
        'passed': passed,
        'total': len(test_cases),
        'results': results,
        'compile_error': None
    }


def _run_python(code_string, input_data, timeout):
    """Run Python code."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False,
                                      encoding='utf-8') as f:
        f.write(code_string)
        temp_path = f.name

    try:
        result = subprocess.run(
            ['python', temp_path],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir()
        )
        return result.stdout, result.stderr if result.returncode != 0 else None
    finally:
        os.unlink(temp_path)


def _run_java(code_string, input_data, timeout):
    """Run Java code — extracts class name from source."""
    import re
    # Try to find public class name
    match = re.search(r'public\s+class\s+(\w+)', code_string)
    class_name = match.group(1) if match else 'Main'

    tmpdir = tempfile.mkdtemp()
    src_path = os.path.join(tmpdir, f'{class_name}.java')

    try:
        with open(src_path, 'w', encoding='utf-8') as f:
            f.write(code_string)

        # Compile
        try:
            compile_result = subprocess.run(
                ['javac', src_path],
                capture_output=True, text=True, timeout=timeout, cwd=tmpdir
            )
        except FileNotFoundError:
            return '', 'Error: Java compiler (javac) not found on system.'

        if compile_result.returncode != 0:
            return '', f'Compilation error: {compile_result.stderr}'

        # Run
        try:
            result = subprocess.run(
                ['java', '-cp', tmpdir, class_name],
                input=input_data,
                capture_output=True, text=True, timeout=timeout, cwd=tmpdir
            )
        except FileNotFoundError:
            return '', 'Error: Java runtime (java) not found on system.'
            
        return result.stdout, result.stderr if result.returncode != 0 else None
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_cpp(code_string, input_data, timeout):
    """Run C++ code."""
    tmpdir = tempfile.mkdtemp()
    src_path = os.path.join(tmpdir, 'solution.cpp')
    exe_path = os.path.join(tmpdir, 'solution.exe' if os.name == 'nt' else 'solution')

    try:
        with open(src_path, 'w', encoding='utf-8') as f:
            f.write(code_string)

        # Compile
        try:
            compile_result = subprocess.run(
                ['g++', '-o', exe_path, src_path, '-std=c++17'],
                capture_output=True, text=True, timeout=timeout, cwd=tmpdir
            )
        except FileNotFoundError:
            return '', 'Error: C++ compiler (g++) not found on system.'

        if compile_result.returncode != 0:
            return '', f'Compilation error: {compile_result.stderr}'

        # Run
        try:
            result = subprocess.run(
                [exe_path],
                input=input_data,
                capture_output=True, text=True, timeout=timeout, cwd=tmpdir
            )
        except FileNotFoundError:
            return '', 'Error: Compiled executable not found or cannot be run.'
            
        return result.stdout, result.stderr if result.returncode != 0 else None
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def analyze_code_style(code_string, language):
    """Perform basic static analysis on code.

    Returns a style score (0-100) and a list of issues found.
    """
    issues = []
    score = 100

    if not code_string or len(code_string.strip()) < 10:
        return 20, ['Code is too short or empty']

    lines = code_string.split('\n')
    total_lines = len(lines)

    # Check for comments
    comment_indicators = {
        'python': '#',
        'java': '//',
        'cpp': '//',
    }
    comment_char = comment_indicators.get(language, '#')
    comment_lines = sum(1 for line in lines if line.strip().startswith(comment_char))
    comment_ratio = comment_lines / max(total_lines, 1)

    if comment_ratio < 0.05:
        issues.append('Very few comments — consider adding documentation')
        score -= 10
    elif comment_ratio > 0.5:
        issues.append('Excessive comments — code should be self-explanatory where possible')
        score -= 5

    # Check line lengths
    long_lines = sum(1 for line in lines if len(line) > 100)
    if long_lines > total_lines * 0.2:
        issues.append(f'{long_lines} lines exceed 100 characters — consider refactoring')
        score -= 10

    # Check for blank line spacing
    consecutive_blanks = 0
    max_consecutive = 0
    for line in lines:
        if line.strip() == '':
            consecutive_blanks += 1
            max_consecutive = max(max_consecutive, consecutive_blanks)
        else:
            consecutive_blanks = 0

    if max_consecutive > 3:
        issues.append('Excessive consecutive blank lines')
        score -= 5

    # Check indentation consistency
    indent_tabs = sum(1 for line in lines if line.startswith('\t') and line.strip())
    indent_spaces = sum(1 for line in lines if line.startswith('    ') and line.strip())
    if indent_tabs > 0 and indent_spaces > 0:
        issues.append('Mixed indentation (tabs and spaces)')
        score -= 10

    # Check for magic numbers (simple heuristic)
    import re
    magic_numbers = re.findall(r'(?<!["\'])\b(?!0\b|1\b|2\b)\d{2,}\b(?!["\'])', code_string)
    if len(magic_numbers) > 3:
        issues.append(f'Found {len(magic_numbers)} magic numbers — consider using named constants')
        score -= 5

    # Language-specific checks
    if language == 'python':
        # Check for proper function naming (snake_case)
        camel_funcs = re.findall(r'def\s+([a-z]+[A-Z]\w*)', code_string)
        if camel_funcs:
            issues.append(f'Function names should use snake_case: {", ".join(camel_funcs[:3])}')
            score -= 5

    if not issues:
        issues.append('Code style looks good!')

    return max(score, 0), issues
