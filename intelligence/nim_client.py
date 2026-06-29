import json
import re

from intelligence.groq_client import GroqClient

PROMPT = """You are a senior cyber threat intelligence analyst producing a formal \
threat advisory. Read the article carefully and extract a detailed, structured \
intelligence report. Be thorough, specific, and analytical. Only use information \
supported by the article — do NOT invent actors, dates, or events. If a field has \
no supporting data, return an empty array [] (or "Unknown").

Respond with ONLY a JSON object, no markdown, no code fences, in exactly this shape:
{{
  "summary": "<5-7 sentence analytical executive summary: what happened, who is affected, how it works, why it matters, broader implications. Full prose.>",
  "severity": "<Critical|High|Medium|Low|Informational>",
  "region": "<geographic region/scope if mentioned, else Unknown>",
  "focus": "<short phrase: the threat's primary focus, e.g. 'Espionage', 'Ransomware', 'Supply-chain compromise'>",
  "motivations": "<actor motivation if known: Financial, Espionage, Hacktivism, etc., else Unknown>",
  "primary_tactics": "<comma-separated high-level tactics, e.g. 'Phishing, DLL side-loading, C2 over HTTPS'>",
  "cves": ["CVE-XXXX-XXXX", ...],
  "threat_actors": ["<actor/group name + short descriptor>", ...],
  "affected_systems": ["<each affected product/vendor/version, specific>", ...],
  "actor_profiles": [
    {{"name": "<actor name>", "description": "<who they are, attribution>", "capabilities": "<tooling, sophistication>", "confirmed_activities": "<what they did in this article>"}}
  ],
  "sector_impacts": [
    {{"sector": "<industry/sector>", "target": "<targeted entity or system>", "actor": "<responsible actor or '-'>", "impact": "<impact or method>"}}
  ],
  "attack_vectors": [
    {{"actor": "<actor or 'General'>", "ttps": "<documented attack vectors, techniques, TTPs>"}}
  ],
  "detection_measures": [
    {{"control": "<detection/mitigation control name>", "description": "<what it does and how it helps, 1-2 sentences>"}}
  ],
  "recommendations": [
    {{"title": "<strategic recommendation>", "description": "<full sentence or two: what to do and why>"}}
  ]
}}

Rules:
- summary: substantial, 5-7 sentences minimum.
- actor_profiles: one object per named actor; [] if none named.
- sector_impacts / attack_vectors: only entries the article supports; [] if none.
- detection_measures AND recommendations: provide at least 4 each, concrete and explained.
- Output ONLY the JSON object.

TITLE: {title}
SOURCE: {source}
ARTICLE:
{body}"""


def _empty(summary="Analysis unavailable."):
    return {
        "summary": summary,
        "severity": "Unknown",
        "region": "Unknown",
        "focus": "Unknown",
        "motivations": "Unknown",
        "primary_tactics": "Unknown",
        "cves": [],
        "threat_actors": [],
        "affected_systems": [],
        "actor_profiles": [],
        "sector_impacts": [],
        "attack_vectors": [],
        "detection_measures": [],
        "recommendations": [],
    }


def _list_of_dicts(value):
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, dict):
            out.append(item)
    return out


class NIMClient:
    """Despite the name, runs analysis via Groq (llama-3.3-70b-versatile)."""

    def __init__(self, client=None):
        self.client = client or GroqClient()

    def analyze(self, title: str, source: str, body: str) -> dict:
        prompt = PROMPT.format(title=title, source=source, body=(body or "")[:8000])

        try:
            raw = self.client.generate(prompt, max_tokens=4000)
        except Exception as e:
            print(f"[NIM/Groq] generate failed: {e!r}")
            return _empty(f"Analysis unavailable (model error: {e}).")

        raw = (raw or "").strip()
        if not raw:
            return _empty("Analysis unavailable (empty response).")

        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 2:
                raw = parts[1]
                if raw.lstrip().lower().startswith("json"):
                    raw = raw.lstrip()[4:]
                raw = raw.strip()

        data = None
        try:
            data = json.loads(raw)
        except Exception:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    data = None

        if not isinstance(data, dict):
            return _empty(raw[:800] or "Analysis unavailable.")

        return {
            "summary": data.get("summary") or "No summary available.",
            "severity": data.get("severity") or "Unknown",
            "region": data.get("region") or "Unknown",
            "focus": data.get("focus") or "Unknown",
            "motivations": data.get("motivations") or "Unknown",
            "primary_tactics": data.get("primary_tactics") or "Unknown",
            "cves": data.get("cves") or [],
            "threat_actors": data.get("threat_actors") or [],
            "affected_systems": data.get("affected_systems") or [],
            "actor_profiles": _list_of_dicts(data.get("actor_profiles")),
            "sector_impacts": _list_of_dicts(data.get("sector_impacts")),
            "attack_vectors": _list_of_dicts(data.get("attack_vectors")),
            "detection_measures": _list_of_dicts(data.get("detection_measures")),
            "recommendations": _list_of_dicts(data.get("recommendations")),
        }