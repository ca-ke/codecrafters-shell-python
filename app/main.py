import sys
import os
import glob

from os.path import basename, isfile
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


def exec(command: str, arguments: List[str]):
    arguments_stringfied = " ".join(arguments)
    call(f"{command} {arguments_stringfied}", shell=True)


def main():
    while True:
        builtin_commands = {"echo", "exit", "type", "pwd"}
        line = input("$ ").split(" ")
        executables = get_executables()

        if not line:
            sys.stdout.write("You shall not pass!")
        else:
            command, arguments = line[0], line[1:]
            if command == "exit":
                return_code = int(arguments[0]) if arguments else 0
                exit(return_code)
            elif command == "echo":
                sys.stdout.write(" ".join(arguments))
                sys.stdout.write("\n")
            elif command == "pwd":
                sys.stdout.write(os.getcwd())
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
