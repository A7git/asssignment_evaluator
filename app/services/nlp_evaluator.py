"""NLP evaluation service — semantic similarity, grammar, and completeness analysis.

This module uses a mock/heuristic-based approach that can be swapped out
for real NLP backends (HuggingFace Transformers, OpenAI, spaCy).
"""
import re
import math
from collections import Counter


def evaluate_similarity(submission_text, reference_text):
    """Compute semantic similarity between submission and reference.

    Uses TF-IDF cosine similarity as a lightweight proxy for
    semantic similarity. Can be replaced with sentence-transformers.

    Returns:
        float: Similarity score 0-100
    """
    if not submission_text or not reference_text:
        return 0.0

    # Tokenize and normalize
    sub_tokens = _tokenize(submission_text)
    ref_tokens = _tokenize(reference_text)

    if not sub_tokens or not ref_tokens:
        return 0.0

    # Build vocabulary
    all_tokens = set(sub_tokens) | set(ref_tokens)

    # TF vectors
    sub_counter = Counter(sub_tokens)
    ref_counter = Counter(ref_tokens)

    # Compute cosine similarity
    dot_product = sum(sub_counter.get(t, 0) * ref_counter.get(t, 0) for t in all_tokens)
    mag_sub = math.sqrt(sum(v ** 2 for v in sub_counter.values()))
    mag_ref = math.sqrt(sum(v ** 2 for v in ref_counter.values()))

    if mag_sub == 0 or mag_ref == 0:
        return 0.0

    cosine_sim = dot_product / (mag_sub * mag_ref)

    # Scale to 0-100
    return round(min(cosine_sim * 100, 100), 1)


def evaluate_grammar(text):
    """Analyze grammar quality of text.

    Heuristic-based scoring that checks:
    - Sentence structure
    - Capitalization
    - Punctuation
    - Spelling patterns

    Returns:
        tuple: (score: float 0-100, issues: list of str)
    """
    if not text or len(text.strip()) < 20:
        return 30.0, ['Text is too short for meaningful grammar analysis']

    issues = []
    score = 100.0

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Check capitalization of sentences
    uncapitalized = sum(1 for s in sentences if s and s[0].islower())
    if uncapitalized > len(sentences) * 0.3:
        issues.append(f'{uncapitalized} sentences start without capitalization')
        score -= 15

    # Check for very long sentences
    long_sentences = sum(1 for s in sentences if len(s.split()) > 40)
    if long_sentences > 0:
        issues.append(f'{long_sentences} sentence(s) are excessively long (>40 words)')
        score -= 10

    # Check for very short sentences that might be fragments
    fragments = sum(1 for s in sentences if 0 < len(s.split()) < 3)
    if fragments > len(sentences) * 0.3:
        issues.append('Multiple sentence fragments detected')
        score -= 10

    # Check for repeated words
    words = text.lower().split()
    for i in range(len(words) - 1):
        if words[i] == words[i + 1] and words[i] not in ('the', 'a', 'an', 'is', 'it', 'to'):
            if f'Repeated word: "{words[i]}"' not in issues:
                issues.append(f'Repeated word: "{words[i]}"')
                score -= 3

    # Check punctuation spacing
    bad_spacing = len(re.findall(r'\w[,;:]\w', text))
    if bad_spacing > 2:
        issues.append('Missing spaces after punctuation marks')
        score -= 8

    # Check for common errors
    common_errors = {
        r'\bthier\b': 'their',
        r'\bteh\b': 'the',
        r'\brecieve\b': 'receive',
        r'\boccured\b': 'occurred',
        r'\bseperately\b': 'separately',
        r'\bdefinately\b': 'definitely',
    }
    for pattern, correction in common_errors.items():
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f'Possible misspelling (did you mean "{correction}"?)')
            score -= 5

    if not issues:
        issues.append('Grammar appears correct')

    return round(max(score, 0), 1), issues


def evaluate_completeness(submission_text, reference_text):
    """Evaluate how complete the submission is relative to the reference.

    Checks for coverage of key concepts/topics from the reference.

    Returns:
        tuple: (score: float 0-100, details: dict)
    """
    if not submission_text or not reference_text:
        return 0.0, {'covered': [], 'missing': [], 'coverage_ratio': 0}

    # Extract key phrases from reference (simple: 2-3 word phrases)
    ref_keywords = _extract_key_phrases(reference_text)
    sub_text_lower = submission_text.lower()

    covered = []
    missing = []

    for phrase in ref_keywords:
        if phrase.lower() in sub_text_lower:
            covered.append(phrase)
        else:
            missing.append(phrase)

    total = len(ref_keywords)
    if total == 0:
        return 50.0, {'covered': [], 'missing': [], 'coverage_ratio': 0.5}

    coverage = len(covered) / total
    score = round(coverage * 100, 1)

    return score, {
        'covered': covered[:10],
        'missing': missing[:10],
        'coverage_ratio': round(coverage, 2)
    }


def evaluate_clarity(text):
    """Evaluate the clarity and readability of text.

    Uses simplified Flesch-Kincaid readability metrics.

    Returns:
        float: Clarity score 0-100
    """
    if not text or len(text.strip()) < 20:
        return 30.0

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()
    syllables = sum(_count_syllables(w) for w in words)

    num_sentences = max(len(sentences), 1)
    num_words = max(len(words), 1)

    # Flesch Reading Ease
    fre = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (syllables / num_words)

    # Normalize to 0-100
    clarity = max(0, min(100, fre))

    # Bonus for proper paragraph structure
    paragraphs = text.split('\n\n')
    if len(paragraphs) > 1:
        clarity = min(100, clarity + 5)

    return round(clarity, 1)


def _tokenize(text):
    """Simple word tokenization with stopword removal."""
    stopwords = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'between', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet', 'both',
        'either', 'neither', 'each', 'every', 'all', 'any', 'few', 'more',
        'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same', 'than',
        'too', 'very', 'just', 'because', 'if', 'when', 'while', 'where',
        'this', 'that', 'these', 'those', 'i', 'me', 'my', 'we', 'our', 'you',
        'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them',
        'their', 'what', 'which', 'who', 'whom', 'how', 'then', 'there', 'here',
    }
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    return [w for w in words if w not in stopwords]


def _extract_key_phrases(text):
    """Extract key single and bi-gram phrases from text."""
    tokens = _tokenize(text)
    counter = Counter(tokens)
    # Return the most common meaningful words
    return [word for word, count in counter.most_common(15) if count >= 1]


def _count_syllables(word):
    """Estimate syllable count in a word."""
    word = word.lower()
    if len(word) <= 3:
        return 1
    vowels = 'aeiou'
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith('e'):
        count -= 1
    return max(count, 1)
