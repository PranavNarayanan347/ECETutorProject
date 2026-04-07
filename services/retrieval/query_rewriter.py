from __future__ import annotations


class QueryRewriter:
    TERM_MAP = {
        "kcl": "kirchhoff current law",
        "kvl": "kirchhoff voltage law",
        "op amp": "operational amplifier",
        "thevenin": "thevenin equivalent",
        "norton": "norton equivalent",
    }

    def rewrite(self, query: str) -> str:
        lowered = query.lower()
        expanded = lowered
        for short, full in self.TERM_MAP.items():
            if short in expanded:
                expanded = expanded.replace(short, full)
        return expanded
