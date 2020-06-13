#!/bin/usr/env python
import mal_types

class NoTokensError(Exception):
    pass


class NotAFunctionError(Exception):
    def __init__(self, val):
        self._val = val

    @property
    def val(self):
        return self._val


class MalSyntaxError(Exception):
    pass


class UnballancedParensError(Exception):
    pass


class UnballancedQuotesError(Exception):
    pass


class UnballancedCurlyBracketsError(Exception):
    pass


class InvalidKeyError(Exception):
    def __init__(self, val):
        self._val = val

    @property
    def val(self):
        return self._val


class MissingValueError(Exception):
    pass


class NoSymbolFoundError(Exception):
    def __init__(self, key: mal_types.Symbol):
        self._key = key.name

    @property
    def val(self):
        return self._key

    def __repr__(self) -> str:
        return f"NoSymbolFoundError(key={self._key!r}"

    def __str__(self) -> str:
        return f"'{self._key}' not found"


class NotASymbolError(Exception):
    def __init__(self, val):
        self._val = val

    @property
    def val(self):
        return self._val


class WrongArgNumberError(Exception):
    def __init__(self, args_num: int):
        self._args_num = args_num
        
    @property
    def args_num(self) -> int:
        return self._args_num


class IndexOutOfRangeError(IndexError):
    pass


class MalTypeError(TypeError):
    def __init__(self, recieved: type, expected: type):
        self._recieved = recieved
        self._expected = expected
        
    @property
    def recieved(self) -> int:
        return self._recieved

    @property
    def expected(self) -> int:
        return self._expected


class NotASequenceError(MalTypeError):
    def __init__(self, val):
        self._val = val

    @property
    def val(self):
        return self._val


class MalExceptionError(Exception):
    def __init__(self, val):
        self._val = val

    @property
    def val(self):
        return self._val
