#!/bin/usr/env python
import exceptions
import mal_types

_VARARGS = mal_types.Symbol("&")

class Env:
    def __init__(self, outer=None, binds=None, exprs=None):
        self.outer = outer
        self.data = {}
        
        if binds:
            for i in range(len(binds)):
                if binds[i] == _VARARGS:
                    self.set(binds[i+1], exprs[i:])
                    break
                else:
                    self.set(binds[i], exprs[i])

    def set(self, key: mal_types.Symbol, value):
        if not isinstance(key, mal_types.Symbol):
            raise exceptions.NotASymbolError(key)
        self.data[key] = value

    def find(self, key: mal_types.Symbol):
        if key in self.data:
            return self
        else:
            return self.outer.find(key) if self.outer is not None else None

    def get(self, key: mal_types.Symbol):
        envinron = self.find(key)
        if envinron is not None:
            return envinron.data[key]

        raise exceptions.NoSymbolFoundError(key)
