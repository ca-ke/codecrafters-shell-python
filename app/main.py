import sys
import os
import glob
import subprocess

from os.path import basename, expanduser, isfile
from typing import Dict
from typing import List


class Tokenizer:
    """
    A simple tokenizer that splits a line into tokens separated by whitespace,
    while allowing quoted strings with single or double quotes and handling
    backslash escapes for certain characters.
    """

    def __init__(self, line: str):
        self.line = line
        self.position = 0
        self.in_single_quotes = False
        self.in_double_quotes = False
        self.current_token_chars = []

    def parse(self) -> List[str]:
        """
        Parse the input line into tokens. Returns a list of strings, each one
        representing a token.
        """
        tokens = []
        while self.position < len(self.line):
            char = self.line[self.position]
            self.position += 1

            if self.in_single_quotes:
                if char == "'":
                    self.in_single_quotes = False
                else:
                    self.current_token_chars.append(char)
            elif self.in_double_quotes:
                if char == '"':
                    self.in_double_quotes = False
                elif char == "\\":
                    escaped = self._handle_escape_in_quotes()
                    self.current_token_chars.append(escaped)
                else:
                    self.current_token_chars.append(char)
            else:
                if char == "'":
                    self.in_single_quotes = True
                elif char == '"':
                    self.in_double_quotes = True
                elif char.isspace():
                    self._finalize_token(tokens)
                elif char == "\\":
                    if self._peek():
                        self.current_token_chars.append(self._next_char())
                    else:
                        self.current_token_chars.append(char)
                else:
                    self.current_token_chars.append(char)

        self._finalize_token(tokens)
        return tokens

    def _handle_escape_in_quotes(self) -> str:
        """
        Handles backslash escapes when inside double quotes.
        """
        next_ch = self._peek()
        if next_ch in ['"', "\\", "$"]:
            return self._next_char()
        return "\\"

    def _finalize_token(self, tokens: List[str]):
        """
        If the current token buffer is not empty, join its characters and
        append to the list of tokens, then reset the buffer.
        """
        if self.current_token_chars:
            tokens.append("".join(self.current_token_chars))
            self.current_token_chars = []

    def _peek(self) -> str:
        """
        Look at the next character without advancing position.
        Returns an empty string if we're at the end.
        """
        if self.position < len(self.line):
            return self.line[self.position]
        return ""

    def _next_char(self) -> str:
        """
        Consume and return the next character in the string.
        Returns an empty string if we're at the end.
        """
        if self.position < len(self.line):
            ch = self.line[self.position]
            self.position += 1
            return ch
        return ""


def get_executables() -> Dict[str, str]:
    executables = {}

    for directory in os.environ["PATH"].split(":"):
        for executable in glob.glob(directory + "/*"):
            if isfile(executable) and basename(executable) not in executables:
                if os.access(executable, os.X_OK):
                    executables[basename(executable)] = directory
    return executables


def exec(command: str, arguments: List[str]):
    try:
        if any(op in arguments for op in [">", "1>", ">>", "1>>"]):
            redirect_position = next(
                (
                    i
                    for i, arg in enumerate(arguments)
                    if arg in [">", "1>", "1>>", ">>"]
                ),
                None,
            )
            if redirect_position is not None and redirect_position + 1 < len(arguments):
                output_file = arguments[redirect_position + 1]
                command_arguments = arguments[:redirect_position]

                operator = arguments[redirect_position]
                file_mode = "w" if operator in [">", "1>"] else "a"
                with open(output_file, file_mode) as file:
                    subprocess.run(
                        [command, *command_arguments], stdout=file, check=True
                    )
            else:
                print("Error: Missing output file for redirection.", file=sys.stderr)

        elif any(op in arguments for op in ["2>", "2>>"]):
            redirect_position = next(
                (i for i, arg in enumerate(arguments) if arg in ["2>", "2>>"]), None
            )
            if redirect_position is not None and redirect_position + 1 < len(arguments):
                error_file = arguments[redirect_position + 1]
                command_arguments = arguments[:redirect_position]

                operator = arguments[redirect_position]
                file_mode = "w" if operator == "2>" else "a"
                with open(error_file, file_mode) as file:
                    subprocess.run(
                        [command, *command_arguments], stderr=file, check=True
                    )
            else:
                print("Error: Missing error file for redirection.", file=sys.stderr)

        else:
            subprocess.run([command, *arguments], check=True)

    except Exception:
        pass


def main():
    while True:
        builtin_commands = {"echo", "exit", "type", "pwd", "cd"}
        line = input("$ ")
        tokenizer = Tokenizer(line).parse()
        executables = get_executables()

        if not line:
            sys.stdout.write("You shall not pass!")
        else:
            command, arguments = (
                tokenizer[0],
                tokenizer[1:],
            )
            if command == "exit":
                return_code = int(arguments[0]) if arguments else 0
                exit(return_code)
            elif command == "pwd":
                sys.stdout.write(os.getcwd())
                sys.stdout.write("\n")
            elif command == "cd":
                directory = arguments[0]
                try:
                    os.chdir(expanduser(directory))
                except FileNotFoundError:
                    sys.stdout.write(f"cd: {directory}: No such file or directory")
                    sys.stdout.write("\n")
            elif command == "type":
                target = arguments[0]
                if target in builtin_commands:
                    sys.stdout.write(f"{target} is a shell builtin")
                    sys.stdout.write("\n")
                else:
                    directory = executables.get(target)

                    if directory:
                        print(f"{target} is {directory}/{target}")
                    else:
                        print(f"{target}: not found")
            else:
                directory = executables.get(command)

                if directory:
                    exec(directory + "/" + command, arguments)
                else:
                    print(f"{command}: command not found")


if __name__ == "__main__":
    main()
