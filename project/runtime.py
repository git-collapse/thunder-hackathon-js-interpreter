"""JavaScript runtime value types and type operations."""

from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from project.environment import Environment


# Sentinel for undefined
class _UndefinedType:
    def __repr__(self):
        return "undefined"

    def __str__(self):
        return "undefined"


UNDEFINED = _UndefinedType()


class JSValue:
    """Base class for JavaScript values."""

    js_type: str = "object"

    def to_js_string(self) -> str:
        return str(self)

    def to_number(self) -> float:
        return float("nan")

    def to_boolean(self) -> bool:
        return True


class JSNull(JSValue):
    js_type = "null"

    def to_js_string(self) -> str:
        return "null"

    def to_number(self) -> float:
        return 0.0

    def to_boolean(self) -> bool:
        return False

    def __repr__(self):
        return "null"


JS_NULL = JSNull()


class JSBoolean(JSValue):
    js_type = "boolean"

    def __init__(self, value: bool):
        self.value = value

    def to_js_string(self) -> str:
        return "true" if self.value else "false"

    def to_number(self) -> float:
        return 1.0 if self.value else 0.0

    def to_boolean(self) -> bool:
        return self.value

    def __repr__(self):
        return "true" if self.value else "false"

    def __eq__(self, other):
        if isinstance(other, JSBoolean):
            return self.value == other.value
        return NotImplemented


class JSNumber(JSValue):
    js_type = "number"

    def __init__(self, value: float):
        self.value = float(value)

    def to_js_string(self) -> str:
        if math.isnan(self.value):
            return "NaN"
        if self.value == float("inf"):
            return "Infinity"
        if self.value == float("-inf"):
            return "-Infinity"
        if self.value == int(self.value) and abs(self.value) < 1e21:
            return str(int(self.value))
        return str(self.value)

    def to_number(self) -> float:
        return self.value

    def to_boolean(self) -> bool:
        return self.value != 0.0 and not math.isnan(self.value)

    def __repr__(self):
        return self.to_js_string()

    def __eq__(self, other):
        if isinstance(other, JSNumber):
            return self.value == other.value
        return NotImplemented


class JSString(JSValue):
    js_type = "string"

    def __init__(self, value: str):
        self.value = str(value)

    def to_js_string(self) -> str:
        return self.value

    def to_number(self) -> float:
        s = self.value.strip()
        if not s:
            return 0.0
        try:
            if s.startswith("0x") or s.startswith("0X"):
                return float(int(s, 16))
            return float(s)
        except ValueError:
            return float("nan")

    def to_boolean(self) -> bool:
        return len(self.value) > 0

    def __repr__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, JSString):
            return self.value == other.value
        return NotImplemented

    def __len__(self):
        return len(self.value)


class JSArray(JSValue):
    js_type = "array"

    def __init__(self, elements: Optional[List[Any]] = None):
        self.elements: List[Any] = list(elements) if elements else []

    @property
    def length(self) -> int:
        return len(self.elements)

    def to_js_string(self) -> str:
        return ",".join(to_display_string(e) for e in self.elements)

    def to_number(self) -> float:
        return float("nan")

    def to_boolean(self) -> bool:
        return True

    def __repr__(self):
        items = ", ".join(to_display_string(e) for e in self.elements)
        return f"[{items}]"

    def __getitem__(self, index):
        if isinstance(index, float):
            index = int(index)
        if index < 0:
            index = len(self.elements) + index
        if 0 <= index < len(self.elements):
            return self.elements[index]
        return UNDEFINED

    def __setitem__(self, index, value):
        if isinstance(index, float):
            index = int(index)
        while len(self.elements) <= index:
            self.elements.append(UNDEFINED)
        self.elements[index] = value

    def __len__(self):
        return len(self.elements)


class JSObject(JSValue):
    js_type = "object"

    def __init__(self, properties: Optional[Dict[str, Any]] = None):
        self.properties: Dict[str, Any] = dict(properties) if properties else {}

    def to_js_string(self) -> str:
        return "[object Object]"

    def to_number(self) -> float:
        return float("nan")

    def to_boolean(self) -> bool:
        return True

    def __repr__(self):
        parts = []
        for k, v in self.properties.items():
            parts.append(f"{k}: {to_display_string(v)}")
        return "{" + ", ".join(parts) + "}"

    def get(self, key: str) -> Any:
        return self.properties.get(key, UNDEFINED)

    def set(self, key: str, value: Any) -> None:
        self.properties[key] = value


class JSFunction(JSValue):
    js_type = "function"

    def __init__(
        self,
        name: str,
        params: List[Any],
        body: Any,
        closure: "Environment",
        is_arrow: bool = False,
        is_expression: bool = False,
    ):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
        self.is_arrow = is_arrow
        self.is_expression = is_expression

    def to_js_string(self) -> str:
        return f"[Function: {self.name or 'anonymous'}]"

    def to_number(self) -> float:
        return float("nan")

    def to_boolean(self) -> bool:
        return True

    def __repr__(self):
        return self.to_js_string()


class JSNativeFunction(JSValue):
    js_type = "function"

    def __init__(self, name: str, fn: Callable, this_binding: Any = None):
        self.name = name
        self.fn = fn
        self.this_binding = this_binding

    def to_js_string(self) -> str:
        return f"[Function: {self.name}]"

    def to_number(self) -> float:
        return float("nan")

    def to_boolean(self) -> bool:
        return True

    def __repr__(self):
        return self.to_js_string()


class JSDate(JSValue):
    js_type = "object"

    def __init__(self, timestamp_ms: float):
        self.timestamp_ms = timestamp_ms

    def to_js_string(self) -> str:
        dt = datetime.utcfromtimestamp(self.timestamp_ms / 1000.0)
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return (
            f"{days[dt.weekday()]} {months[dt.month - 1]} "
            f"{dt.day:02d} {dt.year} "
            f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} GMT+0000 (UTC)"
        )

    def to_number(self) -> float:
        return self.timestamp_ms

    def to_boolean(self) -> bool:
        return True

    def __repr__(self):
        return self.to_js_string()


def wrap(value: Any) -> Any:
    """Wrap a Python value into a JS value if needed."""
    if isinstance(value, JSValue):
        return value
    if value is UNDEFINED or isinstance(value, _UndefinedType):
        return UNDEFINED
    if value is None:
        return JS_NULL
    if isinstance(value, bool):
        return JSBoolean(value)
    if isinstance(value, int) or isinstance(value, float):
        return JSNumber(float(value))
    if isinstance(value, str):
        return JSString(value)
    if isinstance(value, list):
        return JSArray(value)
    if isinstance(value, dict):
        return JSObject(value)
    return value


def unwrap(value: Any) -> Any:
    """Unwrap JS value to Python primitive where possible."""
    if value is UNDEFINED or isinstance(value, _UndefinedType):
        return None
    if isinstance(value, JSNull):
        return None
    if isinstance(value, JSBoolean):
        return value.value
    if isinstance(value, JSNumber):
        return value.value
    if isinstance(value, JSString):
        return value.value
    if isinstance(value, JSArray):
        return value.elements
    if isinstance(value, JSObject):
        return value.properties
    return value


def to_display_string(value: Any) -> str:
    """Format value for console.log output (JavaScript style)."""
    if value is UNDEFINED or isinstance(value, _UndefinedType):
        return "undefined"
    if isinstance(value, JSNull):
        return "null"
    if isinstance(value, JSBoolean):
        return "true" if value.value else "false"
    if isinstance(value, JSNumber):
        return value.to_js_string()
    if isinstance(value, JSString):
        return value.value
    if isinstance(value, JSArray):
        inner = " ".join(to_display_string(v) for v in value.elements)
        # JS console.log prints arrays with spaces in Node
        return inner if False else ",".join(
            _console_format_element(v) for v in value.elements
        )
    if isinstance(value, JSObject):
        return "[object Object]"
    if isinstance(value, (JSFunction, JSNativeFunction)):
        return value.to_js_string()
    if isinstance(value, JSDate):
        return value.to_js_string()
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return JSNumber(value).to_js_string()
    if isinstance(value, str):
        return value
    return str(value)


def _console_format_element(value: Any) -> str:
    if isinstance(value, JSArray):
        inner = ", ".join(_console_format_element(v) for v in value.elements)
        return f"[{inner}]"
    if isinstance(value, JSObject):
        return "[object Object]"
    return to_display_string(value)


def console_log_format(*args) -> str:
    """Format console.log output."""
    parts = []
    for arg in args:
        if isinstance(arg, JSArray):
            inner = ", ".join(_console_format_element(v) for v in arg.elements)
            parts.append(f"[{inner}]")
        elif isinstance(arg, JSObject):
            parts.append("[object Object]")
        elif isinstance(arg, (JSFunction, JSNativeFunction)):
            parts.append(arg.to_js_string())
        else:
            parts.append(to_display_string(arg))
    return " ".join(parts)


def is_truthy(value: Any) -> bool:
    if value is UNDEFINED or isinstance(value, _UndefinedType):
        return False
    if isinstance(value, JSNull):
        return False
    if isinstance(value, JSBoolean):
        return value.value
    if isinstance(value, JSNumber):
        return value.value != 0 and not math.isnan(value.value)
    if isinstance(value, JSString):
        return len(value.value) > 0
    return True


def strict_equal(a: Any, b: Any) -> bool:
    if type(a) != type(b):
        # undefined and null are different types but special
        if (a is UNDEFINED or isinstance(a, _UndefinedType)) and (
            b is UNDEFINED or isinstance(b, _UndefinedType)
        ):
            return True
        if isinstance(a, JSNull) and isinstance(b, JSNull):
            return True
        return False
    if a is UNDEFINED or isinstance(a, _UndefinedType):
        return b is UNDEFINED or isinstance(b, _UndefinedType)
    if isinstance(a, JSNull):
        return isinstance(b, JSNull)
    if isinstance(a, JSBoolean):
        return isinstance(b, JSBoolean) and a.value == b.value
    if isinstance(a, JSNumber):
        if isinstance(b, JSNumber):
            if math.isnan(a.value) or math.isnan(b.value):
                return False
            return a.value == b.value
        return False
    if isinstance(a, JSString):
        return isinstance(b, JSString) and a.value == b.value
    if isinstance(a, JSArray):
        return a is b
    if isinstance(a, JSObject):
        return a is b
    if isinstance(a, (JSFunction, JSNativeFunction)):
        return a is b
    return a == b


def abstract_equal(a: Any, b: Any) -> bool:
    if strict_equal(a, b):
        return True
    # null == undefined
    if (isinstance(a, JSNull) and (b is UNDEFINED or isinstance(b, _UndefinedType))) or (
        isinstance(b, JSNull) and (a is UNDEFINED or isinstance(a, _UndefinedType))
    ):
        return True
    # number vs string
    if isinstance(a, JSNumber) and isinstance(b, JSString):
        return a.value == b.to_number()
    if isinstance(a, JSString) and isinstance(b, JSNumber):
        return a.to_number() == b.value
    # boolean vs other
    if isinstance(a, JSBoolean):
        return abstract_equal(JSNumber(a.to_number()), b)
    if isinstance(b, JSBoolean):
        return abstract_equal(a, JSNumber(b.to_number()))
    # string vs object (not implemented deeply)
    if isinstance(a, (JSString, JSNumber)) and isinstance(b, (JSObject, JSArray)):
        return abstract_equal(a, JSString(str(b)))
    if isinstance(b, (JSString, JSNumber)) and isinstance(a, (JSObject, JSArray)):
        return abstract_equal(JSString(str(a)), b)
    return False


def to_number(value: Any) -> float:
    if value is UNDEFINED or isinstance(value, _UndefinedType):
        return float("nan")
    if isinstance(value, JSNull):
        return 0.0
    if isinstance(value, JSBoolean):
        return 1.0 if value.value else 0.0
    if isinstance(value, JSNumber):
        return value.value
    if isinstance(value, JSString):
        return value.to_number()
    if isinstance(value, JSArray):
        return float("nan")
    if isinstance(value, JSObject):
        return float("nan")
    if isinstance(value, (JSFunction, JSNativeFunction)):
        return float("nan")
    return float("nan")


def to_string(value: Any) -> str:
    if value is UNDEFINED or isinstance(value, _UndefinedType):
        return "undefined"
    if isinstance(value, JSNull):
        return "null"
    if isinstance(value, JSBoolean):
        return "true" if value.value else "false"
    if isinstance(value, JSNumber):
        return value.to_js_string()
    if isinstance(value, JSString):
        return value.value
    if isinstance(value, JSArray):
        return ",".join(to_string(v) for v in value.elements)
    if isinstance(value, JSObject):
        return "[object Object]"
    if isinstance(value, (JSFunction, JSNativeFunction)):
        return value.to_js_string()
    return str(value)


def to_boolean(value: Any) -> bool:
    return is_truthy(value)
