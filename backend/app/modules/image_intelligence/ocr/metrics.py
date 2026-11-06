"""Character Error Rate (CER) and Word Error Rate (WER) evaluation metrics for OCR.

Computes exact normalized Levenshtein edit distance at character and token levels.
"""

from typing import Any


def _levenshtein_distance(
    seq1: list[Any] | str, seq2: list[Any] | str
) -> tuple[int, int, int, int]:
    """Compute edit distance and count of (insertions, deletions, substitutions).

    Returns (total_distance, substitutions, deletions, insertions).
    """
    n = len(seq1)
    m = len(seq2)

    # dp[i][j] = min edits between seq1[:i] and seq2[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],  # deletion
                    dp[i][j - 1],  # insertion
                    dp[i - 1][j - 1],  # substitution
                )

    # Backtrack to identify breakdown
    i, j = n, m
    subs, dels, ins = 0, 0, 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and seq1[i - 1] == seq2[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            dels += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            ins += 1
            j -= 1
        else:
            break

    return dp[n][m], subs, dels, ins


def calculate_cer(reference: str, hypothesis: str, ignore_whitespace: bool = False) -> float:
    """Calculate Character Error Rate: (S + D + I) / N_ref.

    Returns float in range [0.0, 1.0+] where 0.0 is perfect character accuracy.
    """
    ref = reference.strip()
    hyp = hypothesis.strip()

    if ignore_whitespace:
        ref = "".join(ref.split())
        hyp = "".join(hyp.split())

    if not ref:
        return 0.0 if not hyp else 1.0

    dist, _, _, _ = _levenshtein_distance(ref, hyp)
    return round(dist / float(len(ref)), 4)


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate Word Error Rate: (S + D + I) / N_ref_words.

    Returns float in range [0.0, 1.0+] where 0.0 is perfect word accuracy.
    """
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    dist, _, _, _ = _levenshtein_distance(ref_words, hyp_words)
    return round(dist / float(len(ref_words)), 4)


def evaluate_ocr_accuracy(reference: str, hypothesis: str) -> dict[str, Any]:
    """Comprehensive OCR quality report comparing hypothesis against ground truth reference."""
    cer = calculate_cer(reference, hypothesis)
    wer = calculate_wer(reference, hypothesis)

    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()

    word_dist, subs, dels, ins = _levenshtein_distance(ref_words, hyp_words)

    # Accuracy percentage bounded [0.0, 100.0]
    char_accuracy = max(0.0, round((1.0 - cer) * 100.0, 2))
    word_accuracy = max(0.0, round((1.0 - wer) * 100.0, 2))

    return {
        "cer": cer,
        "wer": wer,
        "char_accuracy_pct": char_accuracy,
        "word_accuracy_pct": word_accuracy,
        "reference_char_count": len(reference),
        "hypothesis_char_count": len(hypothesis),
        "reference_word_count": len(ref_words),
        "hypothesis_word_count": len(hyp_words),
        "word_substitutions": subs,
        "word_deletions": dels,
        "word_insertions": ins,
    }
