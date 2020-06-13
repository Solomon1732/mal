#!/bin/usr/env python
import operator
import readline
import sys
#import traceback

import core
import env
import exceptions
import mal_types
import printer
import reader

def is_macro_call(ast, environ: env.Env) -> bool:
    return (
        isinstance(ast, mal_types.List)
        and len(ast) > 0
        and isinstance(ast[0], mal_types.Symbol)
        and environ.find(ast[0]) is not None
        and hasattr(environ.get(ast[0]), "__is_macro__")
    )

def macroexpand(ast, environ: env.Env):
    while is_macro_call(ast, environ):
        macro = environ.get(ast[0])
        ast = macro(*ast[1:])
    return ast

def is_pair(ast) -> bool:
    return core.issequence(ast) and len(ast) > 0

def quasiquote(ast):
    if not is_pair(ast):
        return core.args_to_list(_QUOTE, ast)
    elif ast[0] == _UNQUOTE:
        return ast[1]
    elif is_pair(ast[0]) and ast[0][0] == _SPLICE_UNQUOTE:
        return core.args_to_list(
            mal_types.Symbol("concat"),
            ast[0][1],
            quasiquote(ast[1:]),
        )

    return core.args_to_list(
        mal_types.Symbol("cons"),
        quasiquote(ast[0]),
        quasiquote(ast[1:]),
    )

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

_DEF = mal_types.Symbol("def!")
_LET = mal_types.Symbol("let*")
_DO = mal_types.Symbol("do")
_IF = mal_types.Symbol("if")
_FN = mal_types.Symbol("fn*")
_QUOTE = mal_types.Symbol("quote")
_QUASIQUOTE = mal_types.Symbol("quasiquote")
_UNQUOTE = mal_types.Symbol("unquote")
_SPLICE_UNQUOTE = mal_types.Symbol("splice-unquote")
_DEFMACRO = mal_types.Symbol("defmacro!")
_MACROEXPAND = mal_types.Symbol("macroexpand")
_TRY = mal_types.Symbol("try*")
_CATCH = mal_types.Symbol("catch*")
_PY = mal_types.Symbol("py*")
_PY_STMNT = mal_types.Symbol("py!*")
_DOT = mal_types.Symbol(".")

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

        ast = macroexpand(ast, environ)

        if not isinstance(ast, mal_types.List):
            return eval_ast(ast, environ)
        if len(ast) == 0:
            return ast

        first_elem = ast[0]
        if first_elem == _DEF:
            result = EVAL(ast[2], environ)
            environ.set(ast[1], result)
            return result
        elif first_elem == _LET:
            let_env = env.Env(environ)
            args_list = ast[1]
            args_list_len = len(args_list)
            if args_list_len % 2 != 0:
                raise exceptions.MalSyntaxError("Syntax Error: uneven number of list arguments")
            for i in range(0, args_list_len, 2):
                let_env.set(args_list[i], EVAL(args_list[i+1], environ))
            ast = ast[2]
            environ = let_env
        elif first_elem == _DO:
            eval_ast(ast[1:-1], environ)
            ast = ast[-1]
        elif first_elem == _QUOTE:
            return ast[-1]
        elif first_elem == _QUASIQUOTE:
            ast = quasiquote(ast[1])
        elif first_elem == _IF:
            if len(ast) < 3:
                raise exceptions.MalSyntaxError("Error: missing body")
            cond_ = EVAL(ast[1], environ)
            if cond_ is not None and cond_ is not False:
                ast = ast[2]
            elif len(ast) > 3:
                ast = ast[3]
            else:
                ast = None
        elif first_elem == _TRY:
            if (
                len(ast) < 3
                or not isinstance(ast[2], mal_types.List)
                or len(ast[2]) < 3
                or ast[2][0] != _CATCH
            ):
                return EVAL(ast[1], environ)
            err = None
            try:
                return EVAL(ast[1], environ)
            except exceptions.MalExceptionError as e:
                err = e.val
            except Exception as e:
                err = str(e)
            catch_env = env.Env(environ, (ast[2][1],), (err,))
            return EVAL(ast[2][2], catch_env)
        elif first_elem == _FN:
            if len(ast) < 3:
                raise exceptions.MalSyntaxError("Syntax Error: Missing parameters or body")
            return _function(ast[2], environ, ast[1])
        elif first_elem == _DEFMACRO:
            fn = EVAL(ast[2], environ)
            fn = core.copy_func(fn)
            fn.__is_macro__ = True
            environ.set(ast[1], fn)
            return fn
        elif first_elem == _MACROEXPAND:
            return macroexpand(ast[1], environ)
        elif first_elem == _PY_STMNT:
            exec(compile(ast[1], "", "single"), globals())
            return None
        elif first_elem == _PY:
            return core.py_to_mal(eval(ast[1]))
        elif first_elem == _DOT:
            new_ast = eval_ast(ast[2:], environ)
            fn = eval(ast[1])
            return fn(*new_ast)
        else:
            new_ast = eval_ast(ast, environ)
            fn = new_ast[0]
            if hasattr(fn, "__ast__"):
                ast = fn.__ast__
                environ = fn.__gen_env__(new_ast[1:])
            else:
                return new_ast[0](*new_ast[1:])

def PRINT(tokens) -> str:
    return printer.pr_str(tokens, True)

repl_env = env.Env()

def rep(inpt):
    return PRINT(EVAL(READ(inpt), repl_env))

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def init_env() -> None:
    for k, v in core.ns.items():
        repl_env.set(mal_types.Symbol(k), v)
    repl_env.set(mal_types.Symbol("eval"), lambda ast: EVAL(ast, repl_env))
    repl_env.set(mal_types.Symbol("*ARGV*"), mal_types.List(sys.argv[2:]))
    rep("(def! not (fn* (a) (if a false true)))")
    rep('(def! load-file (fn* (f) (eval (read-string (str "(do " (slurp f) "\nnil)")))))')
    rep('(def! *host-language* "python")')
    rep(
        "(defmacro! cond (fn* (& xs) (if (> (count xs) 0) "
        "(list 'if (first xs) (if (> (count xs) 1) (nth xs 1) "
        "(throw \"odd number of forms to cond\")) (cons 'cond (rest (rest xs)))))))"
    )

def main():
    init_env()

    if len(sys.argv) >= 2:
        rep(f'(load-file "{sys.argv[1]}")')
        sys.exit()

    rep('(println (str "Mal [" *host-language* "]"))')
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
            eprint("Error: Parentheses unbalanced")
        except exceptions.UnballancedQuotesError:
            eprint("Error: Quotes unbalanced")
        except exceptions.UnballancedCurlyBracketsError:
            eprint("Error: Curly brackets unbalanced")
        except exceptions.MalExceptionError as e:
            eprint("Error:", e.val)
        except exceptions.InvalidKeyError as e:
            eprint(f"Error: Invalid Key. Expected string or keyword, got {e.val} instead", file=stderr)
        except exceptions.MissingValueError:
            eprint("Error: Missing value")
        except exceptions.NoSymbolFoundError as e:
            eprint(f"Error: '{e.val}' not found")
        except exceptions.NotASymbolError as e:
            eprint(f"Error: Expected a symbol but found '{type(e.val)}' instead")
        except exceptions.NotAFunctionError as e:
            eprint(f"Error: '{e.val}' is not a function")
        except exceptions.MalSyntaxError as e:
            eprint(e)
        except FileNotFoundError as e:
            eprint("Error: No such file or directory", e.filename)
        except exceptions.IndexOutOfRangeError as e:
            eprint("Error: index out of range:", e)
#        except Exception as e:
#            traceback.print_tb(e)
    readline.write_history_file("/home/user/mal/impls/python.3/.history")


if __name__ == "__main__":
    main()
