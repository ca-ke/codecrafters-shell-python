import sys


def main():
    known_commands = set(["echo", "type", "exit"])
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        splitted_input = input().split(" ")
        command = splitted_input[0]
        arguments = " ".join(splitted_input[1:])

        if command == "exit":
            break
        elif command == "echo":
            sys.stdout.write(arguments)
        elif command == "type":
            if arguments in known_commands:
                sys.stdout.write(f"{arguments} is a shell builtin")
            else:
                sys.stdout.write(f"{arguments}: not found")
        else:
            sys.stdout.write(f"{command}: command not found")
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
