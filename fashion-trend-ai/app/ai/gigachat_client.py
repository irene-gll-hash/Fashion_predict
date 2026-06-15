from __future__ import annotations
from dataclasses import dataclass
from gigachat import GigaChat

@dataclass
class GigaChatClient:
    credentials: str
    scope: str = "GIGACHAT_API_B2B"
    verify_ssl_certs: bool = False
    def analyze(self, prompt: str) -> str:
        with GigaChat(credentials=self.credentials, scope=self.scope, verify_ssl_certs=self.verify_ssl_certs) as client:
            response = client.chat(prompt)
            return response.choices[0].message.content