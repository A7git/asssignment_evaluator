"""Plagiarism detection service — peer-to-peer text comparison."""
import re
from collections import Counter
import math


def check_plagiarism(submission_text, peer_submissions, min_match_length=5):
    """Check a submission against peer submissions for plagiarism.

    Args:
        submission_text: The text/code to check.
        peer_submissions: List of dicts with 'student_id', 'student_name', 'text'.
        min_match_length: Min consecutive matching words to flag.

    Returns:
        dict with originality_score, matches, flagged, disclaimer.
    """
    if not submission_text:
        return {'originality_score': 0.0, 'matches': [], 'flagged': True,
                'disclaimer': 'Submission text is empty.'}

    # Truncate extremely long text to prevent performance hang
    if len(submission_text) > 50000:
        submission_text = submission_text[:50000]

    if not peer_submissions:
        return {'originality_score': 95.0, 'matches': [], 'flagged': False,
                'disclaimer': 'No peer submissions available for comparison.'}

    sub_ngrams = _get_ngrams(submission_text, 4)
    matches = []
    max_sim = 0.0

    for peer in peer_submissions:
        peer_text = peer.get('text', '')
        if not peer_text:
            continue

        peer_ngrams = _get_ngrams(peer_text, 4)
        if not sub_ngrams or not peer_ngrams:
            continue

        overlap = sub_ngrams & peer_ngrams
        overlap_ratio = len(overlap) / max(len(sub_ngrams), 1)
        cosine_sim = _cosine_sim(submission_text, peer_text)
        similarity = int(round((overlap_ratio * 60 + cosine_sim * 0.4), 0))
        max_sim = max(max_sim, similarity)

        if similarity > 20:
            matching = _find_matches(submission_text, peer_text, min_match_length)
            matches.append({
                'peer_id': peer.get('student_id', 'Unknown'),
                'peer_name': peer.get('student_name', 'Unknown'),
                'similarity': similarity,
                'matching_sections': matching[:5]
            })

    matches.sort(key=lambda x: x['similarity'], reverse=True)
    originality = int(round(max(0, 100 - max_sim), 0))

    return {
        'originality_score': originality,
        'matches': matches[:5],
        'flagged': originality < 60,
        'disclaimer': ('Plagiarism detection uses text similarity analysis. '
                       'Results should be reviewed by faculty before action.')
    }


def _get_ngrams(text, n=4):
    words = re.findall(r'\b\w+\b', text.lower())
    return set(tuple(words[i:i+n]) for i in range(len(words)-n+1))


def _cosine_sim(text_a, text_b):
    ca = Counter(re.findall(r'\b\w+\b', text_a.lower()))
    cb = Counter(re.findall(r'\b\w+\b', text_b.lower()))
    tokens = set(ca) | set(cb)
    dot = sum(ca.get(t,0)*cb.get(t,0) for t in tokens)
    ma = math.sqrt(sum(v**2 for v in ca.values()))
    mb = math.sqrt(sum(v**2 for v in cb.values()))
    return (dot/(ma*mb)*100) if ma and mb else 0.0


def _find_matches(text_a, text_b, min_len=5):
    wa = text_a.lower().split()
    wb_set = set(text_b.lower().split())
    matches = []
    i = 0
    wb = text_b.lower().split()
    while i < len(wa):
        best = 0
        for j in range(len(wb)):
            k = 0
            while i+k < len(wa) and j+k < len(wb) and wa[i+k] == wb[j+k]:
                k += 1
            best = max(best, k)
        if best >= min_len:
            matches.append(' '.join(wa[i:i+best]))
            i += best
        else:
            i += 1
    return matches
