import logging
import re
from pathlib import Path
from typing import Optional

import yaml

log = logging.getLogger(__name__)

_PATTERNS_FILE = Path(__file__).parent.parent / "config" / "command_patterns.yaml"
_ENTITIES_FILE = Path(__file__).parent.parent / "config" / "entity_patterns.yaml"


class CommandTranslator:
    """Translate a transcribed utterance into a Home Assistant light command."""

    def __init__(self, ha) -> None:
        self._ha = ha
        self._entities = self._load(_ENTITIES_FILE, "entity_id")
        self._actions = self._load(_PATTERNS_FILE, "action")

    @staticmethod
    def _load(path: Path, value_key: str) -> list[tuple[re.Pattern, str]]:
        with path.open(encoding="utf-8") as fh:
            entries = yaml.safe_load(fh)
        return [(re.compile(e["pattern"], re.I), e[value_key]) for e in entries]


    def translate_and_execute(self, text: str) -> bool:
        entity_id = self._resolve_entity(text)
        if entity_id is None:
            log.debug("No known entity found in: %r", text)
            return False

        action = self._resolve_action(text)
        if action is None:
            log.debug("No recognised action found in: %r", text)
            return False

        log.info("Command: %s → %s", entity_id, action)

        try:
            if action == "turn_on":
                self._ha.turn_on(entity_id)
            elif action == "turn_off":
                self._ha.turn_off(entity_id)
            elif action == "toggle":
                self._ha.toggle(entity_id)
            print(f"  ✓ {action} → {entity_id}")
            return True
        except Exception as exc:  # noqa: BLE001
            log.warning("HA command failed: %s", exc)
            return False


    def _resolve_entity(self, text: str) -> Optional[str]:
        for pattern, entity_id in self._entities:
            if pattern.search(text):
                return entity_id
        if len(self._entities) == 1:
            return self._entities[0][1]
        return None


    def _resolve_action(self, text: str) -> Optional[str]:
        for pattern, action in self._actions:
            if pattern.search(text):
                return action
        return None
