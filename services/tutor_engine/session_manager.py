from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionState:
    hint_level: int = 0
    last_response_type: str = "question"


@dataclass
class SessionManager:
    sessions: dict[str, SessionState] = field(default_factory=dict)

    def get_state(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState()
        return self.sessions[session_id]
