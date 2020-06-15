#!/bin/usr/env python
import copy
import functools
import itertools
import operator
import time
import types
import typing

import exceptions
import mal_types
import printer
import reader
import stepA_mal

def _count(exp) -> int:
    return len(exp) if exp is not None else 0

def _isempty(lst: mal_types.List) -> bool:
    return lst is None or len(lst) == 0

def _pr_str(*args) -> str:
    return " ".join(printer.pr_str(arg, True) for arg in args)

def _str(*args) -> str:
    return "".join(printer.pr_str(arg, False) for arg in args)

def _prn(*args) -> None:
    print(" ".join(printer.pr_str(arg, True) for arg in args))

def _println(*args) -> None:
    print(" ".join(printer.pr_str(arg, False) for arg in args))

def _partial_isinstance(cls: type):
    def istype(arg) -> bool:
        return isinstance(arg, cls)
    return istype

def _partial_is(singleton):
    def _is(arg) -> bool:
        return arg is singleton
    return _is

issequence = _partial_isinstance(mal_types.Sequence)

def _eq_sequence(a: mal_types.Sequence, b: mal_types.Sequence) -> bool:
    assert issequence(a), "a is not a sequence (list or vector)"
    assert issequence(b), "b is not a sequence (list or vector)"

    if len(a) != len(b):
        return False
    for a_item, b_item in zip(a, b):
        if not _eq(a_item, b_item):
            return False
    return True

def _eq_dicts(a, b):
    assert isinstance(a, mal_types.HashMap), "a is not a HashMap"
    assert isinstance(b, mal_types.HashMap), "b is not a HashMap"

    a_keys = sorted(a.keys())
    b_keys = sorted(b.keys())

    if len(a_keys) != len(b_keys):
        return False
    for a_key, b_key in zip(a_keys, b_keys):
        if a_key != b_key:
            return False
        if not _eq(a[a_key], b[b_key]):
            return False
    return True

def _eq(a, b, *_) -> bool:
    if a is b:
        return True
    elif issequence(a) and issequence(b):
        return _eq_sequence(a, b)
    elif isinstance(a, mal_types.HashMap) and isinstance(b, mal_types.HashMap):
        return _eq_dicts(a, b)
    else:
        return a == b

def args_to_list(*args) -> mal_types.List:
    return mal_types.List(args)

def args_to_vector(*args) -> mal_types.Vector:
    return mal_types.Vector(args)

def _slurp(f: str) -> str:
    with open(f) as f:
        return f.read()

def _atom(val) -> mal_types.Atom:
    return mal_types.Atom(val)

def _deref(atom: mal_types.Atom):
    assert isinstance(atom, mal_types.Atom), "not an atom"
    return atom.val

def _reset(atom: mal_types.Atom, val):
    assert isinstance(atom, mal_types.Atom), "not an atom"
    atom.val = val
    return val

def _swap(atom: mal_types.Atom, fn, *args):
    assert isinstance(atom, mal_types.Atom), "not an atom"
    atom.val = fn(atom.val, *args)
    return atom.val

def _add(*args):
    return sum(args)

def _sub(*args):
    args_len = len(args)
    if args_len == 0:
        return 0
    elif args_len == 1:
        return -args[1]
    return functools.reduce(operator.sub, args)

def _mul(*args):
    args_len = len(args)
    if args_len == 0:
        return 0
    elif args_len == 1:
        return args[1]
    return functools.reduce(operator.mul, args)

def _div(*args):
    args_len = len(args)
    if args_len == 0:
        return 0
    elif args_len == 1:
        return 1 // args[1]
    return functools.reduce(operator.floordiv, args)

def _less_than(a, b, *_) -> bool:
    return a < b

def _less_than_eq(a, b, *_) -> bool:
    return a <= b

def _greater_than(a, b, *_) -> bool:
    return a > b

def _greater_than_eq(a, b, *_) -> bool:
    return a >= b

def _cons(arg, sequence: mal_types.Sequence):
    if issequence(sequence):
        return mal_types.List((arg,) + sequence)
    else:
        raise exceptions.NotASequenceError(
            f"Expected a sequence (list or vector) but found a '{type(sequence)}' instead"
        )

def _concat(*args) -> mal_types.List:
    return mal_types.List(itertools.chain(*args))

def _nth(sequence: mal_types.Sequence, i: int):
    if not issequence(sequence):
        raise exceptions.NotASequenceError(sequence)
    try:
        return sequence[i]
    except IndexError as e:
        raise exceptions.IndexOutOfRangeError("nth: index out of range") from e

def _first(sequence: mal_types.Sequence):
    if sequence is not None and not issequence(sequence):
        raise exceptions.NotASequenceError(sequence)
    return sequence[0] if sequence and len(sequence) > 0 else None

def _rest(sequence: mal_types.Sequence):
    if sequence is None:
        return mal_types.List()
    elif not issequence(sequence):
        raise exceptions.NotASequenceError(sequence)
    if len(sequence) == 0:
        return mal_types.List()
    return mal_types.List(sequence[1:])

def throw(obj):
    raise exceptions.MalExceptionError(obj)

def _apply(func: callable, *args):
    return func(*(args[:-1] + args[-1]))

def _map(func: callable, sequence: mal_types.Sequence) -> mal_types.List:
    if not issequence(sequence):
        raise exceptions.NotASequenceError(
            f"Expected a sequence (list or vector0) but found a '{type(sequence)}' instead"
        )
    return mal_types.List(map(func, sequence))

def _args_into_map(hash_map: mal_types.HashMap, *args) -> mal_types.HashMap:
    try:
        for i in range(0, len(args), 2):
            hash_map[args[i]] = args[i+1]
    except IndexError:
        raise exceptions.WrongArgNumberError(len(args)) from e
    return hash_map

def args_to_map(*args) -> mal_types.HashMap:
    new_map = mal_types.HashMap()
    return _args_into_map(new_map, *args)

def _assoc(hash_map: mal_types.HashMap, *args) -> mal_types.HashMap:
    new_map = mal_types.HashMap({**hash_map})
    return _args_into_map(new_map, *args)

def _dissoc(hash_map: mal_types.HashMap, *args) -> mal_types.HashMap:
    new_map = mal_types.HashMap({**hash_map})
    for arg in args:
        new_map.pop(arg, None)
    return new_map

def _get(hash_map: mal_types.HashMap, key: typing.Union[str, mal_types.Keyword]) -> typing.Union[str, mal_types.Keyword]:
    if hash_map is None:
        return None
    if not isinstance(hash_map, mal_types.HashMap):
        raise exceptions.MalTypeError(mal_types.HashMap, type(hash_map))
    if not isinstance(key, str) and not isinstance(key, mal_types.Keyword):
        raise exceptions.MalTypeError(typing.Union[str, mal_types.Keyword], type(key))
    return hash_map.get(key)

def _iscontains(hash_map: mal_types.HashMap, key: typing.Union[str, mal_types.Keyword]) -> bool:
    if not isinstance(hash_map, mal_types.HashMap):
        raise exceptions.MalTypeError(mal_types.HashMap, type(hash_map))
    if not isinstance(key, str) and not isinstance(key, mal_types.Keyword):
        raise exceptions.MalTypeError(typing.Union[str, mal_types.Keyword], type(key))
    return key in hash_map

def _keys(hash_map: mal_types.HashMap) -> mal_types.List:
    if not isinstance(hash_map, mal_types.HashMap):
        raise exceptions.MalTypeError(mal_types.HashMap, type(hash_map))
    return mal_types.List(hash_map.keys())

def _values(hash_map: mal_types.HashMap) -> mal_types.List:
    if not isinstance(hash_map, mal_types.HashMap):
        raise exceptions.MalTypeError(mal_types.HashMap, type(hash_map))
    return mal_types.List(hash_map.values())

def _keyword(keyword: typing.Union[str, mal_types.Keyword]) -> mal_types.Keyword:
    if isinstance(keyword, str):
        return mal_types.Keyword(keyword)
    elif isinstance(keyword, mal_types.Keyword):
        return keyword
    raise exceptions.MalTypeError(typing.Union[str, mal_types.Keyword], type(keyword))

def _readline(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return None

def _time_ms() -> int:
    return int(time.time() * 1000)

def _meta(arg):
    return getattr(arg, "__meta__", None)

def copy_func(fn: callable) -> callable:
    if hasattr(fn, "__code__") and fn.__code__:
        return types.FunctionType(
            fn.__code__,
            fn.__globals__,
            name=fn.__name__,
            argdefs=fn.__defaults__,
            closure=fn.__closure__
        )
    else:
        return types.FunctionType(
            fn.func_code,
            fn.func_globals,
            name=fn.func_name,
            argdefs=fn.func_defaults,
            closure=fn.func_closure
        )

def _clone(obj):
    if isinstance(obj, types.FunctionType):
        return copy_func(obj)
    else:
        return copy.copy(obj)

def _with_meta(obj, meta):
    new_obj = _clone(obj)
    new_obj.__meta__ = meta
    return new_obj

def _seq(seq):
    if seq is None or len(seq) == 0:
        return None
    elif isinstance(seq, mal_types.List):
        return seq
    elif isinstance(seq, mal_types.Vector) or isinstance(seq, str):
        return mal_types.List(seq)
    raise exceptions.MalSyntaxError(f"expected None, List, Vector, or string but got type '{type(seq)}' instead")

def _conj(collection, *args):
    if isinstance(collection, mal_types.List):
        return mal_types.List(args[::-1] + collection)
    if isinstance(collection, mal_types.Vector):
        return mal_types.Vector(collection + args)

def _is_num(obj) -> bool:
    return isinstance(obj, int) and not isinstance(obj, bool)

def _is_func(obj) -> bool:
    return callable(obj) and not hasattr(obj, "__is_macro__")

def _is_macro(obj) -> bool:
    return getattr(obj, "__is_macro__", False)

def py_to_mal(obj):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return mal_types.List(obj)
    elif isinstance(obj, dict):
        return mal_types.HashMap(obj)
    else:
        return obj

ns = {
    "+": _add,
    "-": _sub,
    "*": _mul,
    "/": _div,
    "prn": _prn,
    "list": args_to_list,
    "list?":_partial_isinstance(mal_types.List),
    "empty?": _isempty,
    "count": _count,
    "=": _eq,
    "<": _less_than,
    "<=": _less_than_eq,
    ">": _greater_than,
    ">=": _greater_than_eq,
    "pr-str": _pr_str,
    "println": _println,
    "str": _str,
    "read-string": reader.read_str,
    "slurp":_slurp,
    "atom":_atom,
    "atom?":_partial_isinstance(mal_types.Atom),
    "deref":_deref,
    "reset!":_reset,
    "swap!":_swap,
    "cons":_cons,
    "concat":_concat,
    "nth":_nth,
    "first":_first,
    "rest":_rest,
    "sequential?": issequence,
    "throw":throw,
    "apply":_apply,
    "map":_map,
    "nil?":_partial_is(None),
    "true?":_partial_is(True),
    "false?":_partial_is(False),
    "symbol?":_partial_isinstance(mal_types.Symbol),
    "symbol":mal_types.Symbol,
    "keyword":_keyword,
    "keyword?":_partial_isinstance(mal_types.Keyword),
    "vector":args_to_vector,
    "vector?":_partial_isinstance(mal_types.Vector),
    "hash-map":args_to_map,
    "map?":_partial_isinstance(mal_types.HashMap),
    "assoc":_assoc,
    "dissoc":_dissoc,
    "get":_get,
    "contains?":_iscontains,
    "keys":_keys,
    "vals":_values,
    "readline":_readline,
    "fn?":_is_func,
    "string?":_partial_isinstance(str),
    "number?":_is_num,
    "time-ms":_time_ms,
    "meta":_meta,
    "with-meta":_with_meta,
    "seq":_seq,
    "conj":_conj,
    "macro?":_is_macro,
}
