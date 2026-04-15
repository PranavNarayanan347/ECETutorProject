from __future__ import annotations

import logging
import re

from services.api.config import get_settings

logger = logging.getLogger(__name__)

CIRCUIT_SYSTEM_PROMPT = """\
You are an expert ECE circuit diagram generator. When given a circuit description, \
you produce a clean SVG schematic diagram.

OUTPUT RULES:
- Output ONLY valid SVG markup. No markdown, no explanation, no code fences.
- Start with <svg and end with </svg>.
- Use viewBox="0 0 600 400".
- Use stroke="currentColor" and fill="none" for all components so the diagram \
  adapts to light and dark backgrounds.
- Use fill="currentColor" ONLY for text labels.
- Use stroke-width="2" for wires and components.
- Label every component with its type and value (e.g. R1 = 10kΩ, C1 = 100nF).
- Label nodes with names or voltages where relevant.
- Keep layouts clean: left-to-right or top-to-bottom flow.
- Use dot junctions (small filled circles, r=3) where wires connect.

COMPONENT SYMBOL REFERENCE (use these exact patterns):

Resistor (horizontal, centered at cx,cy, width 40):
  <g transform="translate(cx,cy)">
    <line x1="-30" y1="0" x2="-20" y2="0"/>
    <polyline points="-20,-8 -14,8 -6,-8 2,8 10,-8 16,8 20,0"/>
    <line x1="20" y1="0" x2="30" y2="0"/>
  </g>

Capacitor (horizontal, centered at cx,cy):
  <g transform="translate(cx,cy)">
    <line x1="-25" y1="0" x2="-4" y2="0"/>
    <line x1="-4" y1="-12" x2="-4" y2="12"/>
    <line x1="4" y1="-12" x2="4" y2="12"/>
    <line x1="4" y1="0" x2="25" y2="0"/>
  </g>

Inductor (horizontal, centered at cx,cy):
  <g transform="translate(cx,cy)">
    <line x1="-25" y1="0" x2="-18" y2="0"/>
    <path d="M-18,0 A6,6 0 0,1 -6,0 A6,6 0 0,1 6,0 A6,6 0 0,1 18,0" fill="none"/>
    <line x1="18" y1="0" x2="25" y2="0"/>
  </g>

Voltage source (circle, centered at cx,cy, radius 16):
  <g transform="translate(cx,cy)">
    <circle r="16" fill="none"/>
    <text x="0" y="-4" text-anchor="middle" font-size="10" fill="currentColor">+</text>
    <text x="0" y="10" text-anchor="middle" font-size="10" fill="currentColor">−</text>
    <line x1="0" y1="-16" x2="0" y2="-30"/>
    <line x1="0" y1="16" x2="0" y2="30"/>
  </g>

Current source (circle with arrow, centered at cx,cy):
  <g transform="translate(cx,cy)">
    <circle r="16" fill="none"/>
    <line x1="0" y1="8" x2="0" y2="-8"/>
    <polygon points="0,-8 -4,0 4,0" fill="currentColor"/>
  </g>

Op-amp (triangle, input on left, output on right, centered at cx,cy):
  <g transform="translate(cx,cy)">
    <polygon points="-24,-28 -24,28 28,0" fill="none"/>
    <text x="-18" y="-10" font-size="10" fill="currentColor">+</text>
    <text x="-18" y="14" font-size="10" fill="currentColor">−</text>
  </g>

Ground (3 horizontal lines, attached at top, centered at cx,cy):
  <g transform="translate(cx,cy)">
    <line x1="0" y1="0" x2="0" y2="8"/>
    <line x1="-10" y1="8" x2="10" y2="8"/>
    <line x1="-6" y1="13" x2="6" y2="13"/>
    <line x1="-2" y1="18" x2="2" y2="18"/>
  </g>

Wire junction (filled dot):
  <circle cx="X" cy="Y" r="3" fill="currentColor"/>

DIODE (horizontal, anode left, cathode right):
  <g transform="translate(cx,cy)">
    <line x1="-20" y1="0" x2="-6" y2="0"/>
    <polygon points="-6,-8 -6,8 6,0" fill="none"/>
    <line x1="6" y1="-8" x2="6" y2="8"/>
    <line x1="6" y1="0" x2="20" y2="0"/>
  </g>

IMPORTANT: Produce complete, well-formed SVG. Do not truncate.\
"""

CIRCUIT_KEYWORDS = frozenset([
    "draw", "sketch", "diagram", "schematic", "show me the circuit",
    "circuit for", "draw circuit", "draw_circuit",
])


def needs_circuit(message: str, student_intent: str | None = None) -> bool:
    if student_intent == "draw_circuit":
        return True
    lowered = message.lower()
    return any(kw in lowered for kw in CIRCUIT_KEYWORDS)


class CircuitGenerator:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.anthropic_api_key
        self._model = settings.circuit_model
        self._client = None

    def _get_client(self):
        if self._client is None and self._api_key:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def generate(self, description: str, context: str = "") -> str | None:
        client = self._get_client()
        if client is None:
            logger.info("No Anthropic API key; skipping circuit generation.")
            return None
        try:
            user_msg = f"Draw a circuit diagram for: {description}"
            if context:
                user_msg += f"\n\nRelevant technical context:\n{context[:1500]}"

            response = client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=CIRCUIT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                temperature=0.2,
            )
            raw = response.content[0].text
            return self._extract_svg(raw)
        except Exception as exc:
            logger.warning("Circuit generation failed: %s", exc)
            return None

    @staticmethod
    def _extract_svg(text: str) -> str | None:
        match = re.search(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        if text.strip().startswith("<svg"):
            return text.strip()
        return None
