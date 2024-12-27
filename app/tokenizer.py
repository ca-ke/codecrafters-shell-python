from typing import List


class Tokenizer:
    def __init__(self, line: str):
        self.line = line
        self.position = 0
        self.token = []
        self.in_single_quotes = False
        self.in_double_quotes = False
        self.escape_next = False

    def parse(self) -> List[str]:
        """
        Tokenize the input line, splitting on spaces that aren't inside quotes,
        and handling escapes and mismatched quotes.
        """
        tokens = []

        while self.position < len(self.line):
            char = self.line[self.position]
            self.position += 1

            if self.escape_next:
                self.token.append(char)
                self.escape_next = False
            elif char == "\\":
                self.escape_next = True
            elif char == "'" and not self.in_double_quotes:
                self.in_single_quotes = not self.in_single_quotes
            elif char == '"' and not self.in_single_quotes:
                self.in_double_quotes = not self.in_double_quotes
            elif (
                char == " " and not self.in_single_quotes and not self.in_double_quotes
            ):
                self._finalize_token(tokens)
            else:
                self.token.append(char)
        self._finalize_token(tokens)

        return tokens

    def _finalize_token(self, tokens: List[str]) -> None:
        """Finalize the current token and reset the token buffer."""
        if self.token:
            tokens.append("".join(self.token))
            self.token = []
