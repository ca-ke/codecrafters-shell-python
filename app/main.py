import sys
import os
import glob
import re

from os.path import basename, expanduser, isfile
from typing import Dict
from subprocess import call
from typing import List


def get_executables() -> Dict[str, str]:
    executables = {}

    for directory in os.environ["PATH"].split(":"):
        for executable in glob.glob(directory + "/*"):
            if isfile(executable) and basename(executable) not in executables:
                if os.access(executable, os.X_OK):
                    executables[basename(executable)] = directory
    return executables


def contains_single_quotes(input_string: str) -> bool:
    return bool(re.search(r"'", input_string))


def contains_double_quotes(input_string: str) -> bool:
    return bool(re.search(r"\"", input_string))


def handle_escape_sequences(input_string: str) -> str:
    return re.sub(r'\\(["\\$])', r"\1", input_string)


def exec(command: str, arguments: List[str]):
    arguments_stringfied = " ".join(arguments)
    call(f"{command} {arguments_stringfied}", shell=True)


def main():
    while True:
        builtin_commands = {"echo", "exit", "type", "pwd", "cd"}
        line = input("$ ").split(" ")
        executables = get_executables()

        if not line:
            sys.stdout.write("You shall not pass!")
        else:
            command, arguments = (
                line[0],
                line[1:],
            )

            if command == "exit":
                return_code = int(arguments[0]) if arguments else 0
                exit(return_code)
            elif command == "echo":
                input_string = " ".join(arguments)
                if contains_double_quotes(input_string):
                    quoted_parts = re.findall(r'"([^"]*)"', input_string)
                    quoted_parts_double = [
                        handle_escape_sequences(part) for part in quoted_parts
                    ]
                    sys.stdout.write(" ".join(quoted_parts_double) + "\n")
                elif contains_single_quotes(input_string):
                    quoted_parts = re.findall(r"'([^']*)'", input_string)
                    sys.stdout.write(" ".join(quoted_parts) + "\n")
                else:
                    sys.stdout.write(" ".join(" ".join(arguments).split()) + "\n")
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
