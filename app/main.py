import sys
import os
import glob
import subprocess
import readline

from os.path import basename, expanduser, isfile
from typing import Dict, Optional
from typing import List


class AutoCompleter:
    def __init__(self, builtins: dict, executables: dict):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)

        self.matches = []
        self.commands = sorted(
            set(list(builtins.keys()) + list(executables.keys())),
            key=lambda x: (len(x), x),
        )

    def completer(self, text, state):
        current_word = text.split(" ")[-1]

        if state == 0:
            if current_word:
                self.matches = sorted(
                    [
                        command + " "
                        for command in self.commands
                        if command.startswith(current_word)
                    ]
                )

        try:
            return self.matches[state]
        except IndexError:
            return None


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


class ExecutableFinder:
    def __init__(self, path_env: Optional[str] = None):
        """
        Initialize the ExecutableFinder with an optional PATH environment variable.

        :param path_env: A string representing the PATH environment variable. Defaults to os.environ["PATH"].
        """
        self.path_env = path_env or os.environ.get("PATH", "")

    def get_executables(self) -> Dict[str, str]:
        """
        Finds all executables in the directories listed in the PATH environment variable.

        :return: A dictionary where keys are executable names and values are their directories.
        """
        executables = {}

        for directory in self.path_env.split(":"):
            for executable in glob.glob(directory + "/*"):
                if isfile(executable) and basename(executable) not in executables:
                    if os.access(executable, os.X_OK):
                        executables[basename(executable)] = directory

        return executables


class Command:
    def execute(self, command: str, arguments: List[str]):
        raise NotImplementedError("Subclasses must implement the execute method.")


class ErrorRedirectionCommand(Command):
    def execute(self, command: str, arguments: List[str]):
        redirect_position = next(
            (i for i, arg in enumerate(arguments) if arg in ["2>", "2>>"]),
            None,
        )
        if redirect_position is not None and redirect_position + 1 < len(arguments):
            error_file = arguments[redirect_position + 1]
            command_arguments = arguments[:redirect_position]

            operator = arguments[redirect_position]
            file_mode = "w" if operator == "2>" else "a"
            with open(error_file, file_mode) as file:
                subprocess.run([command, *command_arguments], stderr=file, check=True)
        else:
            print("Error: Missing error file for redirection.", file=sys.stderr)


class OutputRedirectionCommand(Command):
    def execute(self, command: str, arguments: List[str]):
        redirect_position = next(
            (i for i, arg in enumerate(arguments) if arg in [">", "1>", "1>>", ">>"]),
            None,
        )
        if redirect_position is not None and redirect_position + 1 < len(arguments):
            output_file = arguments[redirect_position + 1]
            command_arguments = arguments[:redirect_position]

            operator = arguments[redirect_position]
            file_mode = "w" if operator in [">", "1>"] else "a"
            with open(output_file, file_mode) as file:
                subprocess.run([command, *command_arguments], stdout=file, check=True)
        else:
            print("Error: Missing output file for redirection.", file=sys.stderr)


class StandardOutputCommand(Command):
    def execute(self, command: str, arguments: List[str]):
        subprocess.run([command, *arguments], check=True)


class CommandExecutor:
    def __init__(self):
        self.standard_output_command = StandardOutputCommand()
        self.output_redirection_command = OutputRedirectionCommand()
        self.error_redirection_command = ErrorRedirectionCommand()

    def execute(self, command: str, arguments: List[str]):
        if any(op in arguments for op in [">", "1>", "1>>", ">>"]):
            self.output_redirection_command.execute(command, arguments)
        elif any(op in arguments for op in ["2>", "2>>"]):
            self.error_redirection_command.execute(command, arguments)
        else:
            self.standard_output_command.execute(command, arguments)


def handle_cd(arguments: List[str]):
    if arguments:
        directory = arguments[0]
        try:
            os.chdir(expanduser(directory))
        except FileNotFoundError:
            print(f"cd: {directory}: No such file or directory")
    else:
        print("cd: missing operand")


def handle_type(arguments: List[str], executable_finder: ExecutableFinder):
    """Handle the 'type' command."""
    if arguments:
        target = arguments[0]
        builtin_commands = {"echo", "exit", "type", "pwd", "cd"}
        executables = executable_finder.get_executables()

        if target in builtin_commands:
            print(f"{target} is a shell builtin")
        else:
            directory = executables.get(target)
            if directory:
                print(f"{target} is {directory}/{target}")
            else:
                print(f"{target}: not found")
    else:
        print("type: missing operand")


def main():
    executable_finder = ExecutableFinder()
    command_executor = CommandExecutor()
    builtins = {
        "exit": lambda args: sys.exit(int(args[0]) if args else 0),
        "pwd": lambda _: print(os.getcwd()),
        "cd": lambda args: handle_cd(args),
        "type": lambda args: handle_type(args, executable_finder),
    }

    AutoCompleter(builtins=builtins, executables=executable_finder.get_executables())
    while True:
        line = input("$ ").strip()
        if not line:
            print("You shall not pass!")
            continue

        tokenizer = Tokenizer(line).parse()
        command, arguments = tokenizer[0], tokenizer[1:]

        if command in builtins:
            try:
                builtins[command](arguments)
            except Exception as e:
                print(f"Error: {e}")
        else:
            executables = executable_finder.get_executables()
            directory = executables.get(command)
            if directory:
                try:
                    command_executor.execute(command, arguments)
                except:
                    pass
            else:
                print(f"{command}: command not found")


if __name__ == "__main__":
    main()
