#!/bin/usr/env python
import reader
import mal_types


_SPECIAL_VALS = {
    True:"true",
    False:"false",
    None:"nil",
}

def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

def pr_str(mal_datstruct, print_readably: bool) -> str:
    assert isinstance(print_readably, bool), "print_readably is not of type bool"

    if isinstance(mal_datstruct, str):
        return f'"{_escape(mal_datstruct)}"' if print_readably else mal_datstruct
    elif isinstance(mal_datstruct, dict):
        items = []
        for k, v in mal_datstruct.items():
            items.append(pr_str(k, print_readably))
            items.append(pr_str(v, print_readably))
        return "{" + ' '.join(items) + "}"
    elif isinstance(mal_datstruct, mal_types.Symbol):
        return mal_datstruct.name
    elif isinstance(mal_datstruct, mal_types.Keyword):
        return f":{mal_datstruct.keyword}"
    elif isinstance(mal_datstruct, mal_types.Vector):
        return f"[{(' '.join(pr_str(item, print_readably) for item in mal_datstruct))}]"
    elif isinstance(mal_datstruct, mal_types.List):
        return f"({(' '.join(pr_str(item, print_readably) for item in mal_datstruct))})"
    elif isinstance(mal_datstruct, int) and not isinstance(mal_datstruct, bool):
        return str(mal_datstruct)
    elif callable(mal_datstruct):
        return "# <function>"
    elif isinstance(mal_datstruct, mal_types.Atom):
        return f"(atom {mal_datstruct.val})"
    elif mal_datstruct in _SPECIAL_VALS:
        return _SPECIAL_VALS[mal_datstruct]
    else:
        raise ValueError(mal_datstruct)
