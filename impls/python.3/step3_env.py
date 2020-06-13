#!/bin/usr/env python
import operator
import readline

import env
import exceptions
import mal_types
import printer
import reader


repl_env = env.Env(None)
repl_env.set(mal_types.Symbol("+"), operator.add)
repl_env.set(mal_types.Symbol("-"), operator.sub)
repl_env.set(mal_types.Symbol("*"), operator.mul)
repl_env.set(mal_types.Symbol("/"), operator.floordiv)


def eval_ast(ast, environ: env.Env):
    if isinstance(ast, mal_types.Symbol):
        return environ.get(ast)
    elif isinstance(ast, mal_types.List):
        return mal_types.List(EVAL(item, environ) for item in ast)
    elif isinstance(ast, mal_types.Vector):
        return mal_types.Vector(EVAL(item, environ) for item in ast)
    elif isinstance(ast, mal_types.HashMap):
        return mal_types.HashMap({key:EVAL(value, environ) for key, value in ast.items()})

    return ast

def READ(s: str):
    return reader.read_str(s)

_def = mal_types.Symbol("def!")
_let = mal_types.Symbol("let*")

def EVAL(ast, environ: env.Env):
    if not isinstance(ast, mal_types.List):
        return eval_ast(ast, environ)
    if len(ast) == 0:
        return ast

    first_elem = ast[0]
    if first_elem == _def:
        result = EVAL(ast[2], environ)
        environ.set(ast[1], result)
        return result
    elif first_elem == _let:
        new_env = env.Env(environ)
        args_list = ast[1]
        args_list_len = len(args_list)
        if args_list_len % 2 != 0:
            raise exceptions.MalSyntaxError("Syntax Error: uneven number of list arguments")
        for i in range(0, args_list_len, 2):
            new_env.set(args_list[i], EVAL(args_list[i+1], new_env))
        
        return EVAL(ast[2], new_env)
    else:
        ast = eval_ast(ast, environ)
        try:
            return ast[0](eval_ast(ast[1], environ), eval_ast(ast[2], environ))
        except (TypeError, AttributeError):
            raise NotAFunctionError(ast[0])

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
        except exceptions.NoSymbolFoundError as e:
            print(f"Error: '{e.val}' not found")
        except exceptions.NotASymbolError as e:
            print(f"Error: Expected a symbol but found '{type(e.val)}' instead")
        except exceptions.NotAFunctionError as e:
            print(f"Error: '{e.val}' is not a function")
        except exceptions.MalSyntaxError as e:
            print(e)
    readline.write_history_file("/home/user/mal/impls/python.3/.history")


if __name__ == "__main__":
    main()
