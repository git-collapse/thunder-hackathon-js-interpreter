"""Lexical environment with scope chain support."""

from typing import Any, Dict, Optional


class Binding:
    """A variable binding with mutability control."""

    __slots__ = ("value", "kind", "initialized")

    def __init__(self, value: Any, kind: str = "let"):
        self.value = value
        self.kind = kind  # 'let', 'const', 'var'
        self.initialized = True


class Environment:
    """Scope chain environment for variable lookup and assignment."""

    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.bindings: Dict[str, Binding] = {}

    def define(self, name: str, value: Any, kind: str = "let") -> None:
        if name in self.bindings:
            raise RuntimeError(f"Identifier '{name}' has already been declared")
        self.bindings[name] = Binding(value, kind)

    def assign(self, name: str, value: Any) -> None:
        if name in self.bindings:
            binding = self.bindings[name]
            if binding.kind == "const":
                raise RuntimeError(f"Assignment to constant variable '{name}'")
            binding.value = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise RuntimeError(f"Undefined variable '{name}'")

    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name].value
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError(f"Undefined variable '{name}'")

    def has_local(self, name: str) -> bool:
        return name in self.bindings

    def resolve_binding(self, name: str) -> Optional[Binding]:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.resolve_binding(name)
        return None

    def get_binding_env(self, name: str) -> Optional["Environment"]:
        if name in self.bindings:
            return self
        if self.parent:
            return self.parent.get_binding_env(name)
        return None
