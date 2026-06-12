# parser/normalizer.py
import re


class TextNormalizer:
    """
    Stage 2: Semantic normalization.
    Standardizes CVE IDs, quotes, dashes, and common abbreviations
    so the LLM sees consistent tokens.
    """

    def normalize(self, text: str) -> str:
        text = self._normalize_cve(text)
        text = self._normalize_quotes(text)
        text = self._normalize_dashes(text)
        text = self._normalize_urls(text)
        text = self._normalize_whitespace(text)
        return text

    def _normalize_cve(self, text: str) -> str:
        """Standardize CVE format: cve-2024-1234 → CVE-2024-1234"""
        return re.sub(
            r"\b(?:cve|CVE)[- _](\d{4})[- _](\d{4,7})\b",
            lambda m: f"CVE-{m.group(1)}-{m.group(2)}",
            text,
            flags=re.IGNORECASE,
        )

    def _normalize_quotes(self, text: str) -> str:
        """Replace curly/smart quotes with straight quotes."""
        replacements = {
            "\u2018": "'", "\u2019": "'",   # ' '
            "\u201c": '"', "\u201d": '"',   # " "
            "\u201a": "'", "\u201e": '"',
            "\u2032": "'", "\u2033": '"',
        }
        for curly, straight in replacements.items():
            text = text.replace(curly, straight)
        return text

    def _normalize_dashes(self, text: str) -> str:
        """Replace em/en dashes with hyphens for consistent tokenization."""
        text = text.replace("\u2013", "-").replace("\u2014", " - ")
        return text

    def _normalize_urls(self, text: str) -> str:
        """
        Replace raw URLs with [URL] placeholder.
        Keeps text clean without losing sentence flow.
        Actual URLs are already stored in the DB separately.
        """
        return re.sub(
            r"https?://[^\s<>\"{}|\\^`\[\]]+",
            "[URL]",
            text,
        )

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize multiple spaces, tabs to single space per line."""
        lines = text.splitlines()
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]
        return "\n".join(lines)