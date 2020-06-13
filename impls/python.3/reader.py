#!/bin/usr/env python
import collections
import itertools
import re

import exceptions
import mal_types


class Reader:
    def __init__(self, tokens: list):
        self._tokens = tokens
        self._pos = 0

    def next(self):
        token = self._tokens[self._pos] if len(self._tokens) > 0 else ''
        self._pos += 1
        return token

    def peek(self):
        assert self._pos <= len(self._tokens), "position is more then the number of tokens"
        return self._tokens[self._pos] if len(self._tokens) > 0 else ''

_reg = re.compile(r'''[\s,]*(~@|[\[\]{}()'`~^@]|"(?:\\.|[^\\"])*"?|;.*|[^\s\[\]{}('"`,;)]*)''')

def tokenize(s):
    match = _reg.findall(s)
    if match[-1] == '':
        match.pop()
    return [token for token in match if not token.startswith(";")]

def _is_not_comment(s: str) -> bool:
    return not isinstance(s, str) or not s.startswith(";")

def read_str(s):
    tokens = tokenize(s)
    if len(tokens) == 0:
        raise exceptions.NoTokensError()
    tokens = read_form(Reader(tokens))
    if isinstance(tokens, mal_types.Vector):
        return mal_types.Vector(itertools.takewhile(_is_not_comment, tokens))
    elif isinstance(tokens, mal_types.List):
        return mal_types.List(itertools.takewhile(_is_not_comment, tokens))
    else:
        return tokens

def _is_parens_balanced(s: str) -> str:
    s = s[1:]
    s = s.replace(r'\\', '')
    return s.endswith('"') and not s.endswith(r'\"')

_SPECIAL_VALS = {"true":True, "false":False, "nil":None}

def _unescape(s: str) -> str:
    return s.replace("\\\\", "\u029E").replace('\\"', '"').replace("\\n", "\n").replace("\u029E", "\\")

def read_atom(reader: Reader):
    token = reader.next()

    try:
        return int(token)
    except ValueError:
        pass

    if token in _SPECIAL_VALS:
        token = _SPECIAL_VALS[token]
    elif token.startswith(":"):
        token = mal_types.Keyword(token[1:])
    elif token.startswith('"'):
        if len(token) < 2 or not _is_parens_balanced(token):
            raise exceptions.UnballancedQuotesError()
        token = _unescape(token[1:-1])
    else:
        token = mal_types.Symbol(name=token)

    return token

def _read(end_token, reader: Reader):
    token = read_form(reader)
    while token != end_token:
        yield token
        try:
            token = read_form(reader)
        except IndexError as e:
            raise exceptions.UnballancedParensError()

_END_LIST = mal_types.Symbol(name=")")

def read_list(reader: Reader) -> list:
    return mal_types.List(_read(_END_LIST, reader))

_END_VECTOR = mal_types.Symbol(name="]")

def read_vector(reader: Reader) -> mal_types.Vector:
    return mal_types.Vector(_read(_END_VECTOR, reader))

def _is_valid_key(token) -> bool:
    return isinstance(token, mal_types.Keyword) or isinstance(token, str)

def _is_valid_value(token) -> bool:
    return not isinstance(token, str) or not token == "}"

_END_HASH_MAP = mal_types.Symbol(name="}")

def _yield_dict(reader: Reader):
    key = value = None
    while reader.peek() != "}":
        key = read_form(reader)
        try:
            value = read_form(reader)
        except IndexError:
            raise exceptions.UnballancedCurlyBracketsError()
        if not _is_valid_key(key):
            raise exceptions.InvalidKeyError(key)
        if not _is_valid_value(value):
            raise exceptions.MissingValueError()
        yield (key, value)
    reader.next()

def read_hash_map(reader: Reader) -> mal_types.HashMap:
    return mal_types.HashMap({k:v for k, v in _yield_dict(reader)})

def _quoting(s: str, reader: Reader) -> list:
    return mal_types.List((mal_types.Symbol(s), read_form(reader)))

def read_form(reader: Reader):
    token = reader.peek()
    if token == "(":
        reader.next()
        return read_list(reader)
    elif token == "[":
        reader.next()
        return read_vector(reader)
    elif token == "{":
        reader.next()
        return read_hash_map(reader)
    elif token == "'":
        reader.next()
        return _quoting("quote", reader)
    elif token == "`":
        reader.next()
        return _quoting("quasiquote", reader)
    elif token == "~":
        reader.next()
        return _quoting("unquote", reader)
    elif token == "~@":
        reader.next()
        return _quoting("splice-unquote", reader)
    elif token == "@":
        reader.next()
        return _quoting("deref", reader)
    elif token == "^":
        reader.next()
        token = mal_types.Symbol("with-meta")
        meta = read_form(reader)
        return mal_types.List((token, read_form(reader), meta))
    else:
        return read_atom(reader)
