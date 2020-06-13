#!/bin/usr/env python
import readline


def READ(var):
    return var

def EVAL(var):
    return var

def PRINT(var):
    return var

def rep(inpt):
    return PRINT(EVAL(READ(inpt)))

def main():
    readline.read_history_file("/home/user/mal/impls/python.3/.history")
    while True:
        try:
            line = input("user> ")
        except EOFError:
            print()
            break
        print(rep(line))
    readline.write_history_file("/home/user/mal/impls/python.3/.history")


if __name__ == "__main__":
    main()
