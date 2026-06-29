# parser/cleaner.py
import re
import ftfy


class TextCleaner:
    """
    Stage 1: Raw text cleaning.
    Handles encoding artifacts, HTML residue, and whitespace normalization.
    """

    # Boilerplate phrases common across security news sites
    BOILERPLATE_PATTERNS = [
        r"(?i)subscribe to our newsletter.*",
        r"(?i)follow us on (twitter|linkedin|facebook).*",
        r"(?i)share this article.*",
        r"(?i)related articles?:.*",
        r"(?i)also read:.*",
        r"(?i)advertisement\b.*",
        r"(?i)sponsored content.*",
        r"(?i)click here to.*",
        r"(?i)sign up for.*free.*",
        r"(?i)read more:.*",
        r"(?i)you might also like.*",
        r"(?i)^tags?:.*",
        r"(?i)^categories?:.*",
        r"(?i)^author:.*",          # strip repeated author lines
        r"(?i)^posted (in|by).*",
        r"(?i)\d+ (min|minute) read",
        r"(?i)print this article",
    ]

    def clean(self, text: str) -> str:
        if not text:
            return ""

        # 1. Fix encoding artifacts (mojibake, wrong quotes, etc.)
        text = ftfy.fix_text(text)

        # 2. Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # 3. Remove HTML entity residue that Trafilatura might miss
        text = re.sub(r"&[a-zA-Z]{2,6};", " ", text)
        text = re.sub(r"&#\d+;", " ", text)

        # 4. Remove boilerplate lines
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            if any(re.match(pat, stripped) for pat in self.BOILERPLATE_PATTERNS):
                continue
            cleaned_lines.append(stripped)

        # 5. Collapse multiple blank lines into one
        text = "\n".join(cleaned_lines)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 6. Strip leading/trailing whitespace
        return text.strip()