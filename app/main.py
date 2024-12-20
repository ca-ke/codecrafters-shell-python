from ast import arg
import sys


def main():
    # Uncomment this block to pass the first stage
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        splittedInput = input().split(" ")
        command = splittedInput[0]
        arguments = " ".join(splittedInput[1:])

        if command == "exit":
            break
        elif command == "echo":
            sys.stdout.write(arguments)
            sys.stdout.write("\n")
        else:
            print(f"{command}: command not found")


if __name__ == "__main__":
    main()
