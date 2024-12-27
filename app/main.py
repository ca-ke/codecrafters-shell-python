import sys
import os
import glob
import re

from os.path import basename, expanduser, isfile
from typing import Dict
from subprocess import call
from typing import List

from tokenizer import Tokenizer


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


def handle_escape_sequences(input_string):
    result = []
    i = 0
    while i < len(input_string):
        if input_string[i] == "\\":
            if i + 1 < len(input_string):
                if input_string[i + 1] in ["\\", '"', "'"]:
                    result.append(input_string[i + 1])
                    i += 2
                elif input_string[i + 1] == " ":
                    result.append(" ")
                    i += 2
                else:
                    result.append("\\")
                    i += 1
            else:
                result.append("\\")
                i += 1
        else:
            result.append(input_string[i])
            i += 1
    return "".join(result)


def exec(command: str, arguments: List[str]):
    arguments_stringfied = " ".join(arguments)
    call(f"{command} {arguments_stringfied}", shell=True)


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
            elif command == "echo":
                input_string = " ".join(arguments)
                if contains_double_quotes(input_string):
                    quoted_parts = re.findall(r'"(.*?)(?<!\\)"', input_string)
                    quoted_parts_double = [
                        handle_escape_sequences(part) for part in quoted_parts
                    ]
                    sys.stdout.write(" ".join(quoted_parts_double) + "\n")
                elif contains_single_quotes(input_string):
                    quoted_parts = re.findall(r"'(.*?)(?<!\\)'", input_string)
                    quoted_parts_single = [
                        handle_escape_sequences(part) for part in quoted_parts
                    ]
                    sys.stdout.write(" ".join(quoted_parts_single) + "\n")
                else:
                    parsed_arguments = [
                        handle_escape_sequences(arg) for arg in arguments
                    ]
                    sys.stdout.write(" ".join(parsed_arguments) + "\n")
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
