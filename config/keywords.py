# Fast-track ONLY. Matching = keep without asking the LLM.
# This list can NEVER drop an article; worst case it keeps an extra one.
FAST_TRACK = [
    "ransomware",
    "zero-day",
    "zero day",
    "data breach",
    "actively exploited",
    "critical vulnerability",
    "supply chain attack",
]

# The definition of "relevant" handed to the LLM as your interests.
INTERESTS = [
    "cve",
    "vulnerability",
    "exploit",
    "malware",
    "apt",
    "threat actor",
    "remote code execution",
    "privilege escalation",
    "phishing",
    "backdoor",
]
