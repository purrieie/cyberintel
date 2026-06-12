import intelligence.grok_client as grok_client


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def post(self, url, json, headers, timeout):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return FakeResponse({
            "choices": [{"message": {"content": "Parsed summary"}}]
        })

    def close(self):
        return None


def test_summarize_text_uses_groq_api(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(grok_client.httpx, "Client", FakeClient)

    summary = grok_client.summarize_text("A ransomware gang leaked data after a failed negotiation.")

    assert summary == "Parsed summary"
