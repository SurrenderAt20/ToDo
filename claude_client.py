import json
import re
from typing import Any

import anthropic

from config import get_api_key

SYSTEM_PROMPT = """Du er en effektiv todo-assistent. Du administrerer brugerens opgaveliste.
Du svarer KUN med valid JSON – ingen forklaringer, ingen markdown-blokke, kun rå JSON.

Mulige actions:
- add_task: { "action": "add_task", "data": { "name": "...", "category": "..." | null, "project": "..." | null, "notes": "..." | null } }
- complete_task: { "action": "complete_task", "data": { "task_name": "..." } }
- delete_task: { "action": "delete_task", "data": { "task_name": "..." } }
- update_task: { "action": "update_task", "data": { "task_name": "...", "new_name": "..." | null, "category": "..." | null, "project": "..." | null, "notes": "..." | null } }
- reply: { "action": "reply", "data": { "message": "..." } }

Eksempler på fortolkning:
- "Husk at ringe til Lars vedr. kontrakt" → add_task, category: "arbejde"
- "Tilføj 'skriv referat' til Website redesign projektet" → add_task, project: "Website redesign"
- "Marker den med Lars som færdig" → complete_task
- "Hvad har jeg af tasks?" → reply med opsummering
- "Slet den med referat" → delete_task

Brug altid dansk i reply-beskeder.
Gæt kategori ud fra kontekst hvis ikke angivet.
"""


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


class ClaudeClient:
    def __init__(self) -> None:
        self._client: anthropic.Anthropic | None = None
        self._last_error: str = ""

    def _get_client(self) -> anthropic.Anthropic:
        key = get_api_key()
        if not key:
            raise ValueError("Claude API-nøgle mangler. Åbn indstillinger for at tilføje den.")
        if self._client is None or self._client.api_key != key:
            self._client = anthropic.Anthropic(api_key=key)
        return self._client

    def parse_intent(self, user_message: str, task_list_summary: str) -> dict[str, Any]:
        client = self._get_client()
        context = f"Nuværende opgaver:\n{task_list_summary}\n\nBrugerens besked: {user_message}"
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": context}],
        )
        raw = response.content[0].text
        return _extract_json(raw)

    def test_connection(self) -> bool:
        try:
            client = self._get_client()
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=16,
                messages=[{"role": "user", "content": "ping"}],
            )
            self._last_error = ""
            return True
        except Exception as exc:
            self._last_error = str(exc)
            return False

    @property
    def last_error(self) -> str:
        return self._last_error
