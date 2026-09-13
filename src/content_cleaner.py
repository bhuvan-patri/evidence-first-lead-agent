import re
from collections import Counter


class ContentCleaner:
    """
    Cleans rendered webpage text before it is added to the evidence pack.

    The goal is to reduce navigation/footer boilerplate and repeated text
    while preserving meaningful page content for downstream extraction.
    """

    MIN_LINE_LENGTH = 3
    MAX_LINE_LENGTH = 1000

    def clean(self, text: str) -> str:
        if not text:
            return ""

        lines = self._normalize_lines(text)

        if not lines:
            return ""

        repeated_lines = self._find_repeated_lines(lines)

        cleaned_lines = []

        for line in lines:
            if self._should_skip(line, repeated_lines):
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _normalize_lines(self, text: str) -> list[str]:
        lines = []

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            line = re.sub(r"\s+", " ", line)

            if len(line) < self.MIN_LINE_LENGTH:
                continue

            if len(line) > self.MAX_LINE_LENGTH:
                line = line[: self.MAX_LINE_LENGTH].rstrip()

            lines.append(line)

        return lines

    def _find_repeated_lines(self, lines: list[str]) -> set[str]:
        """
        Repeated lines are often navigation/footer boilerplate.

        We only treat reasonably short repeated lines as boilerplate so that
        repeated legitimate paragraphs are not automatically discarded.
        """
        counts = Counter(lines)

        return {
            line
            for line, count in counts.items()
            if count >= 3 and len(line) <= 150
        }

    def _should_skip(
        self,
        line: str,
        repeated_lines: set[str],
    ) -> bool:
        if line in repeated_lines:
            return True

        if self._looks_like_navigation_fragment(line):
            return True

        return False

    @staticmethod
    def _looks_like_navigation_fragment(line: str) -> bool:
        """
        Remove obvious standalone navigation fragments without filtering
        meaningful sentences that happen to mention the same words.
        """
        navigation_patterns = [
            r"^menu$",
            r"^search$",
            r"^close$",
            r"^login$",
            r"^log in$",
            r"^sign in$",
            r"^sign up$",
            r"^get started$",
            r"^learn more$",
            r"^read more$",
            r"^see all$",
            r"^view all$",
            r"^book a demo$",
            r"^request a demo$",
            r"^subscribe$",
            r"^cookie settings$",
            r"^privacy policy$",
            r"^terms of service$",
        ]

        normalized = line.lower().strip()

        return any(
            re.fullmatch(pattern, normalized)
            for pattern in navigation_patterns
        )