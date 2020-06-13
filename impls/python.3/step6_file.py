#!/bin/usr/env python
import operator
import readline
import sys

import core
import env
import exceptions
import mal_types
import printer
import reader

def eval_ast(ast, environ: env.Env):
    if isinstance(ast, mal_types.Symbol):
        return environ.get(ast)
    elif isinstance(ast, mal_types.List):
        return mal_types.List(EVAL(item, environ) for item in ast)
    elif isinstance(ast, mal_types.Vector):
        return mal_types.Vector(EVAL(item, environ) for item in ast)
    elif isinstance(ast, mal_types.HashMap):
        return mal_types.HashMap({key:EVAL(value, environ) for key, value in ast.items()})
    else:
        return ast

def READ(s: str):
    return reader.read_str(s)

_def = mal_types.Symbol("def!")
_let = mal_types.Symbol("let*")
_do = mal_types.Symbol("do")
_if = mal_types.Symbol("if")
_fn = mal_types.Symbol("fn*")

def _function(ast, environ, params):
    def fn(*args):
        return EVAL(ast, env.Env(environ, params, mal_types.List(args)))
    fn.__meta__ = None
    fn.__ast__ = ast
    fn.__gen_env__ = lambda args: env.Env(environ, params, mal_types.List(args))
    return fn

def EVAL(ast, environ: env.Env):
    while True:
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
            let_env = env.Env(environ)
            args_list = ast[1]
            args_list_len = len(args_list)
            if args_list_len % 2 != 0:
                raise exceptions.MalSyntaxError("Syntax Error: uneven number of list arguments")
            for i in range(0, args_list_len, 2):
                let_env.set(args_list[i], EVAL(args_list[i+1], environ))
            ast = ast[2]
            environ = let_env
        elif first_elem == _do:
            eval_ast(ast[1:-1], environ)
            ast = ast[-1]
        elif first_elem == _if:
            if len(ast) < 3:
                raise exceptions.MalSyntaxError("Error: missing body")
            cond_ = EVAL(ast[1], environ)
            if cond_ is not None and cond_ is not False:
                ast = ast[2]
            elif len(ast) > 3:
                ast = ast[3]
            else:
                ast = None
        elif first_elem == _fn:
            if len(ast) < 3:
                raise exceptions.MalSyntaxError("Syntax Error: Missing parameters or body")
            return _function(ast[2], environ, ast[1])
        else:
            new_ast = eval_ast(ast, environ)
            fn = new_ast[0]
            if hasattr(fn, "__ast__"):
                ast = fn.__ast__
                environ = fn.__gen_env__(new_ast[1:])
            else:
                try:
                    return new_ast[0](*new_ast[1:])
                except TypeError:
                    raise exceptions.NotAFunctionError(new_ast[0])

def PRINT(tokens) -> str:
    return printer.pr_str(tokens, True)

repl_env = env.Env()

def rep(inpt):
    return PRINT(EVAL(READ(inpt), repl_env))

def main():
    for k, v in core.ns.items():
        repl_env.set(mal_types.Symbol(k), v)
    repl_env.set(mal_types.Symbol("eval"), lambda ast: EVAL(ast, repl_env))
    repl_env.set(mal_types.Symbol("*ARGV*"), mal_types.List(sys.argv[2:]))
    rep("(def! not (fn* (a) (if a false true)))")
    rep('(def! load-file (fn* (f) (eval (read-string (str "(do " (slurp f) "\nnil)")))))')
    
    if len(sys.argv) >= 2:
        rep(f'(load-file "{sys.argv[1]}")')
        sys.exit()

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
        except FileNotFoundError as e:
            print("Error: No such file or directory", e.filename)
    readline.write_history_file("/home/user/mal/impls/python.3/.history")


if __name__ == "__main__":
    main()
