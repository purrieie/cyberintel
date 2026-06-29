import json
import re

from config.keywords import FAST_TRACK, INTERESTS

PROMPT = """You are a cybersecurity intelligence filter. An analyst cares about: {interests}.
For EACH article below: decide if it's relevant, AND rate its severity.
Respond with ONLY a JSON array, one object per article, in the same order:
[{{"i": 0, "relevant": true, "severity": "high", "reason": "<max 10 words>"}}, ...]
severity must be one of: "high", "medium", "low".
ARTICLES:
{block}"""


class RelevanceAgent:
    def __init__(self, client=None):
        self.client = client

    def judge_batch(self, articles):
        fast_tracked = []
        uncertain = []
        for article in articles:
            if self._matches_fast_track(article):
                article["severity"] = "high"
                fast_tracked.append(article)
            else:
                uncertain.append(article)

        if not uncertain:
            return fast_tracked

        try:
            kept_uncertain = self._judge_uncertain(uncertain)
        except Exception as e:
            # FAIL-OPEN: keep every uncertain article so we never silently drop.
            print(f"[DEBUG] relevance judge failed, keeping all: {e!r}")
            for article in uncertain:
                article.setdefault("severity", "medium")
            return fast_tracked + uncertain

        return fast_tracked + kept_uncertain

    def _matches_fast_track(self, article):
        if not FAST_TRACK:
            return False
        haystack = " ".join([
            str(article.get("title") or ""),
            str(article.get("raw_text") or ""),
            str(article.get("source") or ""),
        ]).lower()
        return any(keyword.lower() in haystack for keyword in FAST_TRACK)

    def _judge_uncertain(self, articles):
        if self.client:
            client = self.client
        else:
            from intelligence.groq_client import GroqClient
            client = GroqClient()

        prompt = self._build_prompt(articles)
        response = client.generate(prompt, max_tokens=1500)
        verdicts = self._parse_json(response)
        if not isinstance(verdicts, list):
            raise ValueError("verdicts must be a list")

        verdict_by_i = {v["i"]: v for v in verdicts if isinstance(v, dict) and "i" in v}

        keep = []
        for index, article in enumerate(articles):
            verdict = verdict_by_i.get(index)
            if verdict is None:
                # No verdict for this one -> FAIL-OPEN keep it.
                article["severity"] = "medium"
                keep.append(article)
            elif verdict.get("relevant"):
                article["severity"] = self._normalize_severity(verdict.get("severity"))
                keep.append(article)
            # else: explicit not-relevant -> drop
        return keep

    def _build_prompt(self, articles):
        block = json.dumps([
            {
                "i": index,
                "url": article.get("url", ""),
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "text": (article.get("raw_text") or "")[:1800],
            }
            for index, article in enumerate(articles)
        ], ensure_ascii=True)
        return PROMPT.format(interests=", ".join(INTERESTS), block=block)

    def _parse_json(self, text):
        raw = (text or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", raw, flags=re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _normalize_severity(self, severity):
        severity = str(severity or "low").lower()
        if severity not in {"high", "medium", "low"}:
            return "low"
        return severity