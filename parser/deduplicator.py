# parser/deduplicator.py
from datasketch import MinHash
from typing import List

SHINGLE_SIZE = 3          # trigrams
MINHASH_PERMUTATIONS = 64
SIMILARITY_THRESHOLD = 0.75  # paragraphs ≥75% similar are considered duplicates


def _shinglize(text: str, k: int = SHINGLE_SIZE) -> set:
    """Convert text to set of k-gram shingles for MinHash."""
    words = text.lower().split()
    if len(words) < k:
        return {text.lower()}
    return {" ".join(words[i:i+k]) for i in range(len(words) - k + 1)}


def _make_minhash(text: str) -> MinHash:
    m = MinHash(num_perm=MINHASH_PERMUTATIONS)
    for shingle in _shinglize(text):
        m.update(shingle.encode("utf-8"))
    return m


def _jaccard_similarity(m1: MinHash, m2: MinHash) -> float:
    return m1.jaccard(m2)


class ParagraphDeduplicator:
    """
    Stage 3: Near-duplicate paragraph removal using MinHash.

    Why MinHash over exact matching:
      - Security articles frequently reuse boilerplate paragraphs
        with slight wording changes (e.g. "Patch Tuesday" summaries).
      - Exact hash matching misses these.
      - MinHash Jaccard similarity catches near-duplicates efficiently
        without comparing all pairs (O(n) per paragraph).

    Strategy:
      - Split article into paragraphs.
      - For each paragraph, compute MinHash signature.
      - Compare against signatures of already-kept paragraphs.
      - If similarity ≥ threshold, discard as near-duplicate.
    """

    def deduplicate(self, text: str) -> str:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if len(paragraphs) <= 1:
            return text

        kept: List[str] = []
        kept_hashes: List[MinHash] = []

        for para in paragraphs:
            # Skip very short paragraphs (likely headers or one-liners)
            if len(para.split()) < 8:
                kept.append(para)
                continue

            para_hash = _make_minhash(para)
            is_duplicate = False

            for existing_hash in kept_hashes:
                if _jaccard_similarity(para_hash, existing_hash) >= SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept.append(para)
                kept_hashes.append(para_hash)

        return "\n\n".join(kept)