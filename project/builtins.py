"""Built-in objects and native methods for the JavaScript runtime."""

from __future__ import annotations

import math
import random
import re
from datetime import datetime
from typing import Any, Callable, List, TYPE_CHECKING

from project.runtime import (
    JSArray,
    JSBoolean,
    JSDate,
    JSFunction,
    JSNativeFunction,
    JSNull,
    JSNumber,
    JSObject,
    JSString,
    JSValue,
    UNDEFINED,
    console_log_format,
    is_truthy,
    to_boolean,
    to_number,
    to_string,
    wrap,
)

if TYPE_CHECKING:
    from project.interpreter import Interpreter


def _js_str(v: Any) -> str:
    if isinstance(v, JSString):
        return v.value
    return to_string(v)


def _js_num(v: Any) -> float:
    return to_number(v)


def _this_array(args, this_val) -> JSArray:
    if isinstance(this_val, JSArray):
        return this_val
    raise TypeError("Array method called on non-array")


def _this_string(args, this_val) -> JSString:
    if isinstance(this_val, JSString):
        return this_val
    if isinstance(this_val, str):
        return JSString(this_val)
    raise TypeError("String method called on non-string")


# --- Array methods ---

def array_push(interp: "Interpreter", args, this_val):
    arr = _this_array(args, this_val)
    for a in args:
        arr.elements.append(a)
    return JSNumber(len(arr.elements))


def array_pop(interp, args, this_val):
    arr = _this_array(args, this_val)
    if not arr.elements:
        return UNDEFINED
    return arr.elements.pop()


def array_shift(interp, args, this_val):
    arr = _this_array(args, this_val)
    if not arr.elements:
        return UNDEFINED
    return arr.elements.pop(0)


def array_unshift(interp, args, this_val):
    arr = _this_array(args, this_val)
    for i, a in enumerate(args):
        arr.elements.insert(i, a)
    return JSNumber(len(arr.elements))


def array_slice(interp, args, this_val):
    arr = _this_array(args, this_val)
    start = int(_js_num(args[0])) if len(args) > 0 else 0
    end = int(_js_num(args[1])) if len(args) > 1 else len(arr.elements)
    if start < 0:
        start = max(0, len(arr.elements) + start)
    if end < 0:
        end = max(0, len(arr.elements) + end)
    return JSArray(arr.elements[start:end])


def array_splice(interp, args, this_val):
    arr = _this_array(args, this_val)
    start = int(_js_num(args[0])) if len(args) > 0 else 0
    delete_count = int(_js_num(args[1])) if len(args) > 1 else len(arr.elements) - start
    if start < 0:
        start = max(0, len(arr.elements) + start)
    removed = arr.elements[start : start + delete_count]
    insert_items = args[2:]
    arr.elements[start : start + delete_count] = insert_items
    return JSArray(removed)


def array_reverse(interp, args, this_val):
    arr = _this_array(args, this_val)
    arr.elements.reverse()
    return arr


def array_join(interp, args, this_val):
    arr = _this_array(args, this_val)
    sep = _js_str(args[0]) if args else ","
    return JSString(sep.join(to_string(v) for v in arr.elements))


def array_forEach(interp, args, this_val):
    arr = _this_array(args, this_val)
    if not args:
        return UNDEFINED
    callback = args[0]
    for i, item in enumerate(arr.elements):
        interp.call_function(callback, [item, JSNumber(i), arr])
    return UNDEFINED


def array_map(interp, args, this_val):
    arr = _this_array(args, this_val)
    callback = args[0]
    result = []
    for i, item in enumerate(arr.elements):
        result.append(interp.call_function(callback, [item, JSNumber(i), arr]))
    return JSArray(result)


def array_filter(interp, args, this_val):
    arr = _this_array(args, this_val)
    callback = args[0]
    result = []
    for i, item in enumerate(arr.elements):
        val = interp.call_function(callback, [item, JSNumber(i), arr])
        if is_truthy(val):
            result.append(item)
    return JSArray(result)


def array_reduce(interp, args, this_val):
    arr = _this_array(args, this_val)
    callback = args[0]
    start = 0
    if len(args) > 1:
        acc = args[1]
        start = 0
    else:
        if not arr.elements:
            raise TypeError("Reduce of empty array with no initial value")
        acc = arr.elements[0]
        start = 1
    for i in range(start, len(arr.elements)):
        acc = interp.call_function(
            callback, [acc, arr.elements[i], JSNumber(i), arr]
        )
    return acc


def array_length_get(interp, this_val, args):
    arr = _this_array(args, this_val)
    return JSNumber(len(arr.elements))


def array_length_set(interp, this_val, args, value):
    arr = _this_array(args, this_val)
    new_len = int(_js_num(value))
    if new_len < len(arr.elements):
        arr.elements = arr.elements[:new_len]
    else:
        while len(arr.elements) < new_len:
            arr.elements.append(UNDEFINED)
    return value


# --- String methods ---

def string_split(interp, args, this_val):
    s = _this_string(args, this_val).value
    sep = _js_str(args[0]) if args else None
    if sep is None:
        return JSArray([JSString(s)] if s else [])
    if sep == "":
        return JSArray([JSString(c) for c in s])
    parts = s.split(sep)
    return JSArray([JSString(p) for p in parts])


def string_slice(interp, args, this_val):
    s = _this_string(args, this_val).value
    start = int(_js_num(args[0])) if args else 0
    end = int(_js_num(args[1])) if len(args) > 1 else len(s)
    if start < 0:
        start = max(0, len(s) + start)
    if end < 0:
        end = max(0, len(s) + end)
    return JSString(s[start:end])


def string_substring(interp, args, this_val):
    s = _this_string(args, this_val).value
    start = int(_js_num(args[0])) if args else 0
    end = int(_js_num(args[1])) if len(args) > 1 else len(s)
    start = max(0, min(start, len(s)))
    end = max(0, min(end, len(s)))
    if start > end:
        start, end = end, start
    return JSString(s[start:end])


def string_replace(interp, args, this_val):
    s = _this_string(args, this_val).value
    search = _js_str(args[0]) if args else ""
    replacement = _js_str(args[1]) if len(args) > 1 else ""
    return JSString(s.replace(search, replacement, 1))


def string_includes(interp, args, this_val):
    s = _this_string(args, this_val).value
    search = _js_str(args[0]) if args else ""
    return JSBoolean(search in s)


def string_startsWith(interp, args, this_val):
    s = _this_string(args, this_val).value
    search = _js_str(args[0]) if args else ""
    return JSBoolean(s.startswith(search))


def string_endsWith(interp, args, this_val):
    s = _this_string(args, this_val).value
    search = _js_str(args[0]) if args else ""
    return JSBoolean(s.endswith(search))


def string_trim(interp, args, this_val):
    s = _this_string(args, this_val).value
    return JSString(s.strip())


def string_toUpperCase(interp, args, this_val):
    s = _this_string(args, this_val).value
    return JSString(s.upper())


def string_toLowerCase(interp, args, this_val):
    s = _this_string(args, this_val).value
    return JSString(s.lower())


def string_length_get(interp, this_val, args):
    s = _this_string(args, this_val).value
    return JSNumber(len(s))


# --- Math ---

def math_floor(args):
    return JSNumber(math.floor(_js_num(args[0]) if args else float("nan")))


def math_ceil(args):
    return JSNumber(math.ceil(_js_num(args[0]) if args else float("nan")))


def math_round(args):
    return JSNumber(round(_js_num(args[0]) if args else float("nan")))


def math_abs(args):
    return JSNumber(abs(_js_num(args[0]) if args else float("nan")))


def math_pow(args):
    a = _js_num(args[0]) if len(args) > 0 else float("nan")
    b = _js_num(args[1]) if len(args) > 1 else float("nan")
    return JSNumber(a ** b)


def math_max(args):
    if not args:
        return JSNumber(float("-inf"))
    return JSNumber(max(_js_num(a) for a in args))


def math_min(args):
    if not args:
        return JSNumber(float("inf"))
    return JSNumber(min(_js_num(a) for a in args))


def math_random(args):
    return JSNumber(random.random())


# --- Date ---

def date_constructor(interp, args):
    if not args:
        ts = datetime.utcnow().timestamp() * 1000
    elif len(args) == 1:
        val = args[0]
        if isinstance(val, JSString):
            try:
                ts = datetime.fromisoformat(val.value.replace("Z", "")).timestamp() * 1000
            except ValueError:
                ts = _js_num(val)
        else:
            ts = _js_num(val)
    else:
        y = int(_js_num(args[0]))
        m = int(_js_num(args[1]))
        d = int(_js_num(args[2])) if len(args) > 2 else 1
        dt = datetime(y, m + 1, d)
        ts = dt.timestamp() * 1000
    return JSDate(ts)


def date_get_time(interp, this_val, args):
    if isinstance(this_val, JSDate):
        return JSNumber(this_val.timestamp_ms)
    return JSNumber(float("nan"))


def date_now(args):
    return JSNumber(datetime.utcnow().timestamp() * 1000)


# --- Type constructors ---

def js_string_ctor(args):
    if not args:
        return JSString("")
    return JSString(to_string(args[0]))


def js_number_ctor(args):
    if not args:
        return JSNumber(0)
    return JSNumber(to_number(args[0]))


def js_boolean_ctor(args):
    if not args:
        return JSBoolean(False)
    return JSBoolean(is_truthy(args[0]))


def make_array_proto(interp: "Interpreter") -> JSObject:
    proto = JSObject()
    methods = {
        "push": array_push,
        "pop": array_pop,
        "shift": array_shift,
        "unshift": array_unshift,
        "slice": array_slice,
        "splice": array_splice,
        "reverse": array_reverse,
        "join": array_join,
        "forEach": array_forEach,
        "map": array_map,
        "filter": array_filter,
        "reduce": array_reduce,
    }
    for name, fn in methods.items():
        proto.set(name, JSNativeFunction(name, fn))
    return proto


def make_string_proto(interp: "Interpreter") -> JSObject:
    proto = JSObject()
    methods = {
        "split": string_split,
        "slice": string_slice,
        "substring": string_substring,
        "replace": string_replace,
        "includes": string_includes,
        "startsWith": string_startsWith,
        "endsWith": string_endsWith,
        "trim": string_trim,
        "toUpperCase": string_toUpperCase,
        "toLowerCase": string_toLowerCase,
    }
    for name, fn in methods.items():
        proto.set(name, JSNativeFunction(name, fn))
    return proto


def create_global_builtins(interp: "Interpreter") -> dict:
    """Create global scope builtins."""
    output_lines: List[str] = []

    def console_log(interp, args, this_val=None):
        line = console_log_format(*args)
        output_lines.append(line)
        interp.output.append(line)
        return UNDEFINED

    console = JSObject({"log": JSNativeFunction("log", console_log)})

    math_obj = JSObject({
        "floor": JSNativeFunction("floor", lambda interp, a: math_floor(a)),
        "ceil": JSNativeFunction("ceil", lambda interp, a: math_ceil(a)),
        "round": JSNativeFunction("round", lambda interp, a: math_round(a)),
        "abs": JSNativeFunction("abs", lambda interp, a: math_abs(a)),
        "pow": JSNativeFunction("pow", lambda interp, a: math_pow(a)),
        "max": JSNativeFunction("max", lambda interp, a: math_max(a)),
        "min": JSNativeFunction("min", lambda interp, a: math_min(a)),
        "random": JSNativeFunction("random", lambda interp, a: math_random(a)),
    })

    date_obj = JSObject({
        "now": JSNativeFunction("now", lambda interp, a: date_now(a)),
    })

    return {
        "console": console,
        "Math": math_obj,
        "Date": JSNativeFunction("Date", lambda interp, a: date_constructor(interp, a)),
        "String": JSNativeFunction("String", lambda interp, a: js_string_ctor(a)),
        "Number": JSNativeFunction("Number", lambda interp, a: js_number_ctor(a)),
        "Boolean": JSNativeFunction("Boolean", lambda interp, a: js_boolean_ctor(a)),
        "parseInt": JSNativeFunction("parseInt", lambda interp, a: JSNumber(int(_js_num(a[0])) if a else float("nan"))),
        "parseFloat": JSNativeFunction("parseFloat", lambda interp, a: JSNumber(_js_num(a[0]) if a else float("nan"))),
        "isNaN": JSNativeFunction("isNaN", lambda interp, a: JSBoolean(math.isnan(_js_num(a[0]) if a else float("nan")))),
        "Array": JSNativeFunction("Array", lambda interp, a: JSArray(list(a))),
        "_array_proto": make_array_proto(interp),
        "_string_proto": make_string_proto(interp),
    }
