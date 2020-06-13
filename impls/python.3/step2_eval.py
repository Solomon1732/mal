#!/bin/usr/env python
import operator
import readline

import exceptions
import mal_types
import printer
import reader


class NoSuchSymbolError(Exception):
    pass


class NotAFunctionError(Exception):
    pass


repl_env = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.floordiv
}

def eval_ast(ast, env: dict):
    if isinstance(ast, mal_types.Symbol):
        try:
            return env[ast.name]
        except KeyError:
            raise NoSuchSymbolError(ast.name)
    elif isinstance(ast, mal_types.List):
        return mal_types.List(EVAL(item, env) for item in ast)
    elif isinstance(ast, mal_types.Vector):
        return mal_types.Vector(EVAL(item, env) for item in ast)
    elif isinstance(ast, mal_types.HashMap):
        return mal_types.HashMap({key:EVAL(value, env) for key, value in ast.items()})

    return ast

def READ(s: str):
    return reader.read_str(s)

def EVAL(ast, env: dict):
    if isinstance(ast, mal_types.List):
        if len(ast) == 0:
            return ast

        try:
            ast = eval_ast(ast, env)
            return ast[0](ast[1], ast[2])
        except KeyError:
            raise NoSuchSymbolError(ast)
        except (TypeError, AttributeError):
            raise NotAFunctionError(ast[0])
    else:
        return eval_ast(ast, env)

def PRINT(tokens) -> str:
    return printer.pr_str(tokens, True)

def rep(inpt):
    return PRINT(EVAL(READ(inpt), repl_env))

def main():
    readline.read_history_file("/home/user/mal/impls/python.3/.history")
    while True:
        try:
            line = input("user> ")
        except EOFError:
            print("EOF")
            break
        try:
            print(rep(line))
        except exceptions.NoTokensError:
            continue
        except exceptions.UnballancedParensError:
            print("Error: Parentheses unbalanced")
        except exceptions.UnballancedQuotesError:
            print("Error: Quotes unbalanced")
        except exceptions.UnballancedCurlyBracketsError:
            print("Error: Curly brackets unbalanced")
        except exceptions.InvalidKeyError as e:
            print(f"Error: Invalid Key. Expected string or keyword, got {e.val} instead")
        except exceptions.MissingValueError:
            print("Error: Missing value")
        except NoSuchSymbolError as e:
            print(f"Error: '{e.args[0]}' not found")
        except NotAFunctionError as e:
            print(f"Error: '{e.args[0]}' is not a function")
    readline.write_history_file("/home/user/mal/impls/python.3/.history")


if __name__ == "__main__":
    main()
