#!/bin/usr/env python
import collections
import typing


class Sequence(tuple):
    def __add__(self, rhs):
        return Sequence(super().__add__(rhs))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Sequence(super().__getitem__(key))
        else:
            return super().__getitem__(key)

    def __getslice__(self, *args):
        return Sequence(super().__getslice__(*args))


class Vector(Sequence):
    def __add__(self, rhs):
        return Vector(super().__add__(rhs))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Vector(super().__getitem__(key))
        else:
            return super().__getitem__(key)

    def __getslice__(self, *args):
        return Vector(super().__getslice__(*args))


class List(Sequence):
    def __add__(self, rhs):
        return List(super().__add__(rhs))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return List(super().__getitem__(key))
        else:
            return super().__getitem__(key)

    def __getslice__(self, *args):
        return List(super().__getslice__(*args))


class Symbol(typing.NamedTuple):
    name: str


class Keyword(typing.NamedTuple):
    keyword: str


class Atom:
    def __init__(self, val):
        self._val = val

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, value) -> None:
        self._val = value


class HashMap(dict):
    pass
