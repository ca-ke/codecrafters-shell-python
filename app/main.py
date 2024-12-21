import sys
import os


def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        splitted_input = input().split(" ")
        command = splitted_input[0]
        arguments = " ".join(splitted_input[1:])
        path_variable = os.environ["PATH"]
        builtin_commands = {"echo", "exit", "type"}

        if command == "exit":
            break
        elif command == "echo":
            sys.stdout.write(arguments)
        elif command == "type":
            if arguments in builtin_commands:
                sys.stdout.write(f"{arguments} is a shell builtin")
            else:
                folders = path_variable.split(":")
                found = False
                for folder in reversed(folders):
                    try:
                        dir_contents = [
                            x for x in os.listdir(folder) if x.startswith(arguments)
                        ]
                        if dir_contents:
                            sys.stdout.write(f"{arguments} is {folder}/{arguments}")
                            found = True
                            break
                    except FileNotFoundError:
                        found = False
                if not found:
                    sys.stdout.write(f"{arguments}: not found")
        else:
            sys.stdout.write(f"{command}: command not found")
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
