import logging
import os
from typing import Optional

import requests

log = logging.getLogger(__name__)

_TOKEN_ENV_VAR = "HA_TOKEN"


class HomeAssistant:
    """Send commands to Home Assistant entities via the REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8123",
        token: Optional[str] = None,
        timeout: float = 5.0,
    ):
        resolved_token = token or os.environ.get(_TOKEN_ENV_VAR)
        if not resolved_token:
            raise ValueError(
                f"No Home Assistant token provided. "
                f"Pass token= or set the {_TOKEN_ENV_VAR} environment variable."
            )
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {resolved_token}",
                "Content-Type": "application/json",
            }
        )
        log.debug("HARemote ready — %s", self._base_url)

    def turn_on(self, entity_id: str, *, transition: Optional[float] = None) -> dict:
        payload: dict = {"entity_id": entity_id}
        if transition is not None:
            payload["transition"] = transition
        return self._call_service("light", "turn_on", payload)

    def turn_off(self, entity_id: str, *, transition: Optional[float] = None) -> dict:
        payload: dict = {"entity_id": entity_id}
        if transition is not None:
            payload["transition"] = transition
        return self._call_service("light", "turn_off", payload)

    def toggle(self, entity_id: str) -> dict:
        return self._call_service("light", "toggle", {"entity_id": entity_id})

    def get_state(self, entity_id: str) -> dict:
        url = f"{self._base_url}/api/states/{entity_id}"
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        return response.json()

    def is_on(self, entity_id: str) -> bool:
        state = self.get_state(entity_id)
        return state.get("state") == "on"

    def close(self) -> None:
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _call_service(self, domain: str, service: str, payload: dict) -> dict:
        url = f"{self._base_url}/api/services/{domain}/{service}"
        log.debug("POST %s  payload=%s", url, payload)
        response = self._session.post(url, json=payload, timeout=self._timeout)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <entity_id> [on|off|toggle]")
        sys.exit(1)

    entity = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "toggle"

    with HomeAssistant(base_url="http://192.168.242.21:8123") as ctrl:
        if command == "on":
            result = ctrl.turn_on(entity)
        elif command == "off":
            result = ctrl.turn_off(entity)
        else:
            result = ctrl.toggle(entity)
        print(result)
