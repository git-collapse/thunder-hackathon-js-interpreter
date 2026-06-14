"""Abstract Syntax Tree node definitions."""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(kw_only=True)
class Node:
    line: int = 0
    column: int = 0


@dataclass(kw_only=True)
class Program(Node):
    body: List[Node] = field(default_factory=list)


@dataclass(kw_only=True)
class BlockStatement(Node):
    body: List[Node] = field(default_factory=list)


@dataclass(kw_only=True)
class VariableDeclaration(Node):
    kind: str  # 'let', 'const', 'var'
    declarations: List["VariableDeclarator"] = field(default_factory=list)


@dataclass(kw_only=True)
class VariableDeclarator(Node):
    id: "Identifier"
    init: Optional[Node] = None


@dataclass(kw_only=True)
class AssignmentExpression(Node):
    operator: str
    left: Node
    right: Node


@dataclass(kw_only=True)
class Identifier(Node):
    name: str


@dataclass(kw_only=True)
class Literal(Node):
    value: Any


@dataclass(kw_only=True)
class BinaryExpression(Node):
    operator: str
    left: Node
    right: Node


@dataclass(kw_only=True)
class UnaryExpression(Node):
    operator: str
    argument: Node
    prefix: bool = True


@dataclass(kw_only=True)
class LogicalExpression(Node):
    operator: str
    left: Node
    right: Node


@dataclass(kw_only=True)
class UpdateExpression(Node):
    operator: str  # '++' or '--'
    argument: Node
    prefix: bool = True


@dataclass(kw_only=True)
class MemberExpression(Node):
    object: Node
    property: Node
    computed: bool = False


@dataclass(kw_only=True)
class CallExpression(Node):
    callee: Node
    arguments: List[Node] = field(default_factory=list)


@dataclass(kw_only=True)
class IfStatement(Node):
    test: Node
    consequent: Node
    alternate: Optional[Node] = None


@dataclass(kw_only=True)
class WhileStatement(Node):
    test: Node
    body: Node


@dataclass(kw_only=True)
class ForStatement(Node):
    init: Optional[Node]
    test: Optional[Node]
    update: Optional[Node]
    body: Node


@dataclass(kw_only=True)
class ForInOfStatement(Node):
    left: Node
    right: Node
    body: Node
    kind: str  # 'in' or 'of'


@dataclass(kw_only=True)
class BreakStatement(Node):
    pass


@dataclass(kw_only=True)
class ContinueStatement(Node):
    pass


@dataclass(kw_only=True)
class SwitchCase(Node):
    test: Optional[Node]
    consequent: List[Node] = field(default_factory=list)


@dataclass(kw_only=True)
class SwitchStatement(Node):
    discriminant: Node
    cases: List[SwitchCase] = field(default_factory=list)


@dataclass(kw_only=True)
class ConditionalExpression(Node):
    test: Node
    consequent: Node
    alternate: Node


@dataclass(kw_only=True)
class FunctionDeclaration(Node):
    id: Identifier
    params: List[Node]  # Identifier or RestElement
    body: BlockStatement
    async_: bool = False


@dataclass(kw_only=True)
class FunctionExpression(Node):
    id: Optional[Identifier]
    params: List[Node]
    body: BlockStatement
    async_: bool = False


@dataclass(kw_only=True)
class ArrowFunctionExpression(Node):
    params: List[Node]
    body: Node  # BlockStatement or expression
    async_: bool = False


@dataclass(kw_only=True)
class RestElement(Node):
    argument: Identifier


@dataclass(kw_only=True)
class ReturnStatement(Node):
    argument: Optional[Node] = None


@dataclass(kw_only=True)
class ExpressionStatement(Node):
    expression: Node


@dataclass(kw_only=True)
class ArrayExpression(Node):
    elements: List[Optional[Node]] = field(default_factory=list)


@dataclass(kw_only=True)
class ObjectExpression(Node):
    properties: List["Property"] = field(default_factory=list)


@dataclass(kw_only=True)
class Property(Node):
    key: Node  # Identifier or Literal
    value: Node
    computed: bool = False
    kind: str = "init"  # init, get, set


@dataclass(kw_only=True)
class SpreadElement(Node):
    argument: Node


@dataclass(kw_only=True)
class TemplateLiteral(Node):
    parts: List[Any] = field(default_factory=list)


@dataclass(kw_only=True)
class EmptyStatement(Node):
    pass
