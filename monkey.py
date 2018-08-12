import sys
import getpass
from monkey import repl


def main():
    print(
        f"Hello {getpass.getuser()}! This is the Moneky programming language!")
    print("Feel free to type in commands")
    repl.start(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
