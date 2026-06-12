# intelligence/batch_processor.py
import os
from db.repository import ArticleRepository
from intelligence.groq_client import GroqClient

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def load_template(name: str) -> str:
    path = os.path.join(TEMPLATE_DIR, f"{name}.txt")
    with open(path, "r") as f:
        return f.read()


class BatchProcessor:
    def __init__(self):
        self.repo = ArticleRepository()
        self.client = GroqClient()

    def process_parsed(self, batch_size: int = 5, template: str = "threat_summary"):
        articles = self.repo.get_parsed_unsent(limit=batch_size)
        if not articles:
            print("No new parsed articles to send to Groq.")
            return

        combined = "\n\n---\n\n".join(
            f"Title: {a['title']}\nSource: {a['source']}\nContent: {a['clean_text'][:2000]}"
            for a in articles
        )

        prompt_template = load_template(template)
        prompt = prompt_template.format(articles=combined)

        result = self.client.generate(prompt)

        for a in articles:
            self.repo.update_grok_summary(a["id"], result)

        print(f"Sent {len(articles)} articles to Groq. Summary stored.")
        return result