"""Tree-walking interpreter for JavaScript AST."""

from __future__ import annotations

import math
from typing import Any, List, Optional

from project import ast_nodes as ast
from project.builtins import create_global_builtins
from project.environment import Environment
from project.errors import (
    BreakSignal,
    ContinueSignal,
    ReturnSignal,
    RuntimeError as JSRuntimeError,
)
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
    UNDEFINED,
    JS_NULL,
    abstract_equal,
    is_truthy,
    strict_equal,
    to_number,
    to_string,
    wrap,
)


class Interpreter:
    """Evaluate JavaScript AST nodes."""

    def __init__(self):
        self.global_env = Environment(is_function_scope=True)
        self.env = self.global_env
        self.output: List[str] = []
        self._builtins = create_global_builtins(self)
        for name, value in self._builtins.items():
            if not name.startswith("_"):
                self.global_env.define(name, value, "var")

    def run(self, program: ast.Program) -> List[str]:
        self.output = []
        self._hoist_declarations(program.body, self.global_env)
        self._execute_block(program.body, self.global_env)
        return self.output

    def _hoist_declarations(self, statements: List[ast.Node], env: Environment):
        for stmt in statements:
            if isinstance(stmt, ast.FunctionDeclaration):
                self.env = env
                self._eval_function_declaration(stmt)
            elif isinstance(stmt, ast.VariableDeclaration) and stmt.kind == "var":
                for decl in stmt.declarations:
                    if not env.has_local(decl.id.name):
                        env.define(decl.id.name, UNDEFINED, "var")
            elif isinstance(stmt, ast.BlockStatement):
                self._hoist_declarations(stmt.body, env)
            elif isinstance(stmt, ast.IfStatement):
                if isinstance(stmt.consequent, ast.BlockStatement):
                    self._hoist_declarations(stmt.consequent.body, env)
                if stmt.alternate and isinstance(stmt.alternate, ast.BlockStatement):
                    self._hoist_declarations(stmt.alternate.body, env)
            elif isinstance(stmt, ast.ForStatement):
                if isinstance(stmt.init, ast.VariableDeclaration) and stmt.init.kind == "var":
                    for decl in stmt.init.declarations:
                        if not env.has_local(decl.id.name):
                            env.define(decl.id.name, UNDEFINED, "var")
                if isinstance(stmt.body, ast.BlockStatement):
                    self._hoist_declarations(stmt.body.body, env)
            elif isinstance(stmt, ast.ForInOfStatement):
                if isinstance(stmt.left, ast.VariableDeclaration) and stmt.left.kind == "var":
                    for decl in stmt.left.declarations:
                        if not env.has_local(decl.id.name):
                            env.define(decl.id.name, UNDEFINED, "var")
                if isinstance(stmt.body, ast.BlockStatement):
                    self._hoist_declarations(stmt.body.body, env)
            elif isinstance(stmt, ast.WhileStatement):
                if isinstance(stmt.body, ast.BlockStatement):
                    self._hoist_declarations(stmt.body.body, env)
            elif isinstance(stmt, ast.SwitchStatement):
                for case in stmt.cases:
                    self._hoist_declarations(case.consequent, env)

    def _execute_block(self, statements: List[ast.Node], env: Environment):
        prev = self.env
        self.env = env
        try:
            for stmt in statements:
                self._execute(stmt)
        finally:
            self.env = prev

    def _execute(self, node: ast.Node) -> Any:
        if node is None:
            return UNDEFINED

        if isinstance(node, ast.Program):
            return self._execute_block(node.body, self.env)

        if isinstance(node, ast.BlockStatement):
            child_env = Environment(self.env)
            return self._execute_block(node.body, child_env)

        if isinstance(node, ast.VariableDeclaration):
            return self._eval_variable_declaration(node)

        if isinstance(node, ast.ExpressionStatement):
            return self._evaluate(node.expression)

        if isinstance(node, ast.IfStatement):
            return self._eval_if(node)

        if isinstance(node, ast.WhileStatement):
            return self._eval_while(node)

        if isinstance(node, ast.ForStatement):
            return self._eval_for(node)

        if isinstance(node, ast.ForInOfStatement):
            return self._eval_for_in_of(node)

        if isinstance(node, ast.SwitchStatement):
            return self._eval_switch(node)

        if isinstance(node, ast.FunctionDeclaration):
            return self._eval_function_declaration(node)

        if isinstance(node, ast.BreakStatement):
            raise BreakSignal()

        if isinstance(node, ast.ContinueStatement):
            raise ContinueSignal()

        if isinstance(node, ast.ReturnStatement):
            val = UNDEFINED
            if node.argument:
                val = self._evaluate(node.argument)
            raise ReturnSignal(val)

        if isinstance(node, ast.EmptyStatement):
            return UNDEFINED

        return self._evaluate(node)

    def _eval_variable_declaration(self, node: ast.VariableDeclaration):
        for decl in node.declarations:
            value = UNDEFINED
            if decl.init:
                value = self._evaluate(decl.init)
            name = decl.id.name
            if node.kind == "var":
                self._define_var(name, value)
            else:
                if self.env.has_local(name):
                    raise JSRuntimeError(f"Identifier '{name}' has already been declared")
                self.env.define(name, value, node.kind)
        return UNDEFINED

    def _define_var(self, name: str, value: Any):
        env = self.env
        while env.parent and not env.is_function_scope:
            env = env.parent
        if env.has_local(name):
            env.bindings[name].value = value
        else:
            env.define(name, value, "var")

    def _eval_function_declaration(self, node: ast.FunctionDeclaration):
        fn = JSFunction(
            name=node.id.name,
            params=node.params,
            body=node.body,
            closure=self.env,
        )
        if node.id.name:
            if self.env.has_local(node.id.name):
                self.env.assign(node.id.name, fn)
            else:
                self.env.define(node.id.name, fn, "var")
        return fn

    def _eval_if(self, node: ast.IfStatement):
        if is_truthy(self._evaluate(node.test)):
            return self._execute(node.consequent)
        if node.alternate:
            return self._execute(node.alternate)
        return UNDEFINED

    def _eval_while(self, node: ast.WhileStatement):
        result = UNDEFINED
        while is_truthy(self._evaluate(node.test)):
            try:
                result = self._execute(node.body)
            except ContinueSignal:
                continue
            except BreakSignal:
                break
        return result

    def _eval_for(self, node: ast.ForStatement):
        loop_env = Environment(self.env)
        prev = self.env
        self.env = loop_env
        try:
            if node.init:
                if isinstance(node.init, ast.VariableDeclaration):
                    self._eval_variable_declaration(node.init)
                else:
                    self._evaluate(node.init)
            while True:
                if node.test and not is_truthy(self._evaluate(node.test)):
                    break
                try:
                    self._execute(node.body)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                if node.update:
                    self._evaluate(node.update)
        finally:
            self.env = prev
        return UNDEFINED

    def _eval_for_in_of(self, node: ast.ForInOfStatement):
        values = self._iteration_values(self._evaluate(node.right), node.kind)
        loop_env = Environment(self.env)
        prev = self.env
        self.env = loop_env
        try:
            for value in values:
                self._bind_iteration_target(node.left, value)
                try:
                    self._execute(node.body)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        finally:
            self.env = prev
        return UNDEFINED

    def _iteration_values(self, value: Any, kind: str) -> List[Any]:
        if kind == "of":
            if isinstance(value, JSArray):
                return list(value.elements)
            if isinstance(value, JSString):
                return [JSString(ch) for ch in value.value]
            raise JSRuntimeError("Value is not iterable")
        if kind == "in":
            if isinstance(value, JSArray):
                return [JSString(str(i)) for i in range(len(value.elements))]
            if isinstance(value, JSString):
                return [JSString(str(i)) for i in range(len(value.value))]
            if isinstance(value, JSObject):
                return [JSString(k) for k in value.properties.keys()]
            raise JSRuntimeError("Cannot iterate properties of value")
        raise JSRuntimeError(f"Unknown for-loop kind: {kind}")

    def _bind_iteration_target(self, target: ast.Node, value: Any):
        if isinstance(target, ast.VariableDeclaration):
            decl = target.declarations[0]
            name = decl.id.name
            if target.kind == "var":
                self._define_var(name, value)
                return
            if self.env.has_local(name):
                self.env.bindings[name].value = value
            else:
                self.env.define(name, value, target.kind)
            return
        if isinstance(target, ast.Identifier):
            self._assign(target.name, value)
            return
        if isinstance(target, ast.MemberExpression):
            obj = self._evaluate(target.object)
            key = self._member_key(target)
            self._set_property(obj, key, value)
            return
        raise JSRuntimeError("Invalid for-loop target")

    def _eval_switch(self, node: ast.SwitchStatement):
        discriminant = self._evaluate(node.discriminant)
        start_index = None
        default_index = None
        for i, case in enumerate(node.cases):
            if case.test is None:
                default_index = i
            elif strict_equal(discriminant, self._evaluate(case.test)):
                start_index = i
                break
        if start_index is None:
            start_index = default_index
        if start_index is None:
            return UNDEFINED
        try:
            for case in node.cases[start_index:]:
                for stmt in case.consequent:
                    self._execute(stmt)
        except BreakSignal:
            return UNDEFINED
        return UNDEFINED

    def _evaluate(self, node: ast.Node) -> Any:
        if node is None:
            return UNDEFINED

        if isinstance(node, ast.Literal):
            return self._eval_literal(node)

        if isinstance(node, ast.Identifier):
            return self.env.get(node.name)

        if isinstance(node, ast.BinaryExpression):
            return self._eval_binary(node)

        if isinstance(node, ast.UnaryExpression):
            return self._eval_unary(node)

        if isinstance(node, ast.LogicalExpression):
            return self._eval_logical(node)

        if isinstance(node, ast.AssignmentExpression):
            return self._eval_assignment(node)

        if isinstance(node, ast.ConditionalExpression):
            if is_truthy(self._evaluate(node.test)):
                return self._evaluate(node.consequent)
            return self._evaluate(node.alternate)

        if isinstance(node, ast.UpdateExpression):
            return self._eval_update(node)

        if isinstance(node, ast.MemberExpression):
            return self._eval_member(node)

        if isinstance(node, ast.CallExpression):
            return self._eval_call(node)

        if isinstance(node, ast.ArrayExpression):
            return self._eval_array(node)

        if isinstance(node, ast.ObjectExpression):
            return self._eval_object(node)

        if isinstance(node, ast.TemplateLiteral):
            return self._eval_template_literal(node)

        if isinstance(node, ast.FunctionExpression):
            return JSFunction(
                name=node.id.name if node.id else "",
                params=node.params,
                body=node.body,
                closure=self.env,
                is_expression=True,
            )

        if isinstance(node, ast.ArrowFunctionExpression):
            return JSFunction(
                name="",
                params=node.params,
                body=node.body,
                closure=self.env,
                is_arrow=True,
            )

        if isinstance(node, ast.BlockStatement):
            child_env = Environment(self.env)
            return self._execute_block(node.body, child_env)

        raise JSRuntimeError(f"Unknown node type: {type(node).__name__}")

    def _eval_literal(self, node: ast.Literal) -> Any:
        v = node.value
        if v is None:
            return JS_NULL
        if v == "undefined":
            return UNDEFINED
        if isinstance(v, bool):
            return JSBoolean(v)
        if isinstance(v, (int, float)):
            return JSNumber(float(v))
        if isinstance(v, str):
            return JSString(v)
        return wrap(v)

    def _eval_binary(self, node: ast.BinaryExpression) -> Any:
        if node.operator == "==":
            return JSBoolean(abstract_equal(
                self._evaluate(node.left), self._evaluate(node.right)
            ))
        if node.operator == "===":
            return JSBoolean(strict_equal(
                self._evaluate(node.left), self._evaluate(node.right)
            ))
        if node.operator == "!=":
            return JSBoolean(not abstract_equal(
                self._evaluate(node.left), self._evaluate(node.right)
            ))
        if node.operator == "!==":
            return JSBoolean(not strict_equal(
                self._evaluate(node.left), self._evaluate(node.right)
            ))

        left = self._evaluate(node.left)
        right = self._evaluate(node.right)

        if node.operator in ("+", "-", "*", "/", "%", "**"):
            if node.operator == "+" and (
                isinstance(left, JSString) or isinstance(right, JSString)
            ):
                return JSString(to_string(left) + to_string(right))
            a = to_number(left)
            b = to_number(right)
            ops = {
                "+": lambda x, y: x + y,
                "-": lambda x, y: x - y,
                "*": lambda x, y: x * y,
                "/": lambda x, y: x / y,
                "%": lambda x, y: x % y,
                "**": lambda x, y: x ** y,
            }
            return JSNumber(ops[node.operator](a, b))

        if node.operator in ("<", "<=", ">", ">="):
            a = self._compare_values(left, right)
            b = self._compare_values(right, left)
            if node.operator == "<":
                return JSBoolean(a < 0)
            if node.operator == "<=":
                return JSBoolean(a <= 0)
            if node.operator == ">":
                return JSBoolean(a > 0)
            if node.operator == ">=":
                return JSBoolean(a >= 0)

        raise JSRuntimeError(f"Unknown binary operator: {node.operator}")

    def _compare_values(self, left, right) -> int:
        if isinstance(left, JSString) and isinstance(right, JSString):
            if left.value < right.value:
                return -1
            if left.value > right.value:
                return 1
            return 0
        a = to_number(left)
        b = to_number(right)
        if math.isnan(a) or math.isnan(b):
            return 0
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    def _eval_unary(self, node: ast.UnaryExpression) -> Any:
        if node.operator == "typeof":
            return JSString(self._typeof(node.argument))
        arg = self._evaluate(node.argument)
        if node.operator == "!":
            return JSBoolean(not is_truthy(arg))
        if node.operator == "-":
            return JSNumber(-to_number(arg))
        if node.operator == "+":
            return JSNumber(to_number(arg))
        raise JSRuntimeError(f"Unknown unary operator: {node.operator}")

    def _typeof(self, argument: ast.Node) -> str:
        if isinstance(argument, ast.Identifier) and self.env.resolve_binding(argument.name) is None:
            return "undefined"
        value = self._evaluate(argument)
        if value is UNDEFINED:
            return "undefined"
        if isinstance(value, JSBoolean):
            return "boolean"
        if isinstance(value, JSNumber):
            return "number"
        if isinstance(value, JSString):
            return "string"
        if isinstance(value, (JSFunction, JSNativeFunction)):
            return "function"
        if isinstance(value, (JSNull, JSObject, JSArray, JSDate)):
            return "object"
        return "undefined"

    def _eval_logical(self, node: ast.LogicalExpression) -> Any:
        if node.operator == "||":
            left = self._evaluate(node.left)
            if is_truthy(left):
                return left
            return self._evaluate(node.right)
        if node.operator == "&&":
            left = self._evaluate(node.left)
            if not is_truthy(left):
                return left
            return self._evaluate(node.right)
        raise JSRuntimeError(f"Unknown logical operator: {node.operator}")

    def _eval_assignment(self, node: ast.AssignmentExpression) -> Any:
        right_val = self._evaluate(node.right)

        if isinstance(node.left, ast.Identifier):
            name = node.left.name
            if node.operator == "=":
                self._assign(name, right_val)
                return right_val
            current = self.env.get(name)
            new_val = self._compound_assign(current, node.operator, right_val)
            self._assign(name, new_val)
            return new_val

        if isinstance(node.left, ast.MemberExpression):
            obj = self._evaluate(node.left.object)
            key = self._member_key(node.left)
            if node.operator == "=":
                self._set_property(obj, key, right_val)
                return right_val
            current = self._get_property(obj, key)
            new_val = self._compound_assign(current, node.operator, right_val)
            self._set_property(obj, key, new_val)
            return new_val

        raise JSRuntimeError("Invalid assignment target")

    def _compound_assign(self, current, op: str, right_val) -> Any:
        op_map = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%"}
        if op not in op_map:
            raise JSRuntimeError(f"Unknown assignment operator: {op}")
        bin_op = op_map[op]
        if bin_op == "+" and (isinstance(current, JSString) or isinstance(right_val, JSString)):
            return JSString(to_string(current) + to_string(right_val))
        return self._binary_num(to_number(current), bin_op, to_number(right_val))

    def _binary_num(self, a: float, op: str, b: float) -> JSNumber:
        ops = {"+": a + b, "-": a - b, "*": a * b, "/": a / b, "%": a % b}
        return JSNumber(ops[op])

    def _assign(self, name: str, value: Any):
        self.env.assign(name, value)

    def _eval_update(self, node: ast.UpdateExpression) -> Any:
        if isinstance(node.argument, ast.Identifier):
            name = node.argument.name
            current = self.env.get(name)
            num = to_number(current)
            delta = 1 if node.operator == "++" else -1
            new_val = JSNumber(num + delta)
            self._assign(name, new_val)
            return new_val if node.prefix else JSNumber(num)
        raise JSRuntimeError("Invalid update expression target")

    def _member_key(self, node: ast.MemberExpression) -> str:
        if node.computed:
            val = self._evaluate(node.property)
            return to_string(val)
        if isinstance(node.property, ast.Identifier):
            return node.property.name
        if isinstance(node.property, ast.Literal):
            return str(node.property.value)
        return to_string(self._evaluate(node.property))

    def _eval_member(self, node: ast.MemberExpression) -> Any:
        obj = self._evaluate(node.object)
        key = self._member_key(node)
        return self._get_property(obj, key)

    def _get_property(self, obj: Any, key: str) -> Any:
        if isinstance(obj, JSArray):
            if key == "length":
                return JSNumber(len(obj.elements))
            idx = self._parse_index(key)
            if idx is not None:
                return obj[idx]
            proto = self._builtins.get("_array_proto")
            if proto and key in proto.properties:
                method = proto.properties[key]
                if isinstance(method, JSNativeFunction):
                    bound = JSNativeFunction(method.name, method.fn)
                    bound.this_binding = obj
                    return bound
        if isinstance(obj, JSString):
            if key == "length":
                return JSNumber(len(obj.value))
            idx = self._parse_index(key)
            if idx is not None:
                if 0 <= idx < len(obj.value):
                    return JSString(obj.value[idx])
                return UNDEFINED
            proto = self._builtins.get("_string_proto")
            if proto and key in proto.properties:
                method = proto.properties[key]
                if isinstance(method, JSNativeFunction):
                    bound = JSNativeFunction(method.name, method.fn)
                    bound.this_binding = obj
                    return bound
        if isinstance(obj, JSObject):
            return obj.get(key)
        if isinstance(obj, JSNativeFunction) and key in obj.properties:
            return obj.properties[key]
        if isinstance(obj, JSDate):
            if key == "getTime":
                from project.builtins import date_get_time
                return JSNativeFunction("getTime", lambda interp, a, tv=obj: date_get_time(interp, tv, a))
        idx = self._parse_index(key)
        if idx is not None and isinstance(obj, JSArray):
            return obj[idx]
        return UNDEFINED

    def _set_property(self, obj: Any, key: str, value: Any) -> None:
        if isinstance(obj, JSArray):
            if key == "length":
                new_len = int(to_number(value))
                if new_len < len(obj.elements):
                    obj.elements = obj.elements[:new_len]
                else:
                    while len(obj.elements) < new_len:
                        obj.elements.append(UNDEFINED)
                return
            idx = self._parse_index(key)
            if idx is not None:
                while len(obj.elements) <= idx:
                    obj.elements.append(UNDEFINED)
                obj.elements[idx] = value
                return
        if isinstance(obj, JSObject):
            obj.set(key, value)
            return
        if isinstance(obj, JSArray):
            idx = self._parse_index(key)
            if idx is not None:
                obj[idx] = value
                return
        raise JSRuntimeError(f"Cannot set property '{key}' on value")

    def _eval_template_literal(self, node: ast.TemplateLiteral) -> JSString:
        chunks = []
        for part in node.parts:
            if isinstance(part, str):
                chunks.append(part)
            else:
                chunks.append(to_string(self._evaluate(part)))
        return JSString("".join(chunks))

    def _parse_index(self, key: str) -> Optional[int]:
        try:
            return int(key)
        except ValueError:
            return None

    def _eval_call(self, node: ast.CallExpression) -> Any:
        callee = self._evaluate(node.callee)
        args = [self._evaluate(a) for a in node.arguments]

        # Method call: obj.method()
        if isinstance(node.callee, ast.MemberExpression):
            this_val = self._evaluate(node.callee.object)
            if isinstance(callee, JSNativeFunction):
                callee.this_binding = this_val
            return self.call_function(callee, args, this_val)

        return self.call_function(callee, args)

    def call_function(self, callee: Any, args: List[Any], this_val: Any = None) -> Any:
        if isinstance(callee, JSNativeFunction):
            this_binding = this_val if this_val is not None else callee.this_binding
            try:
                if this_binding is not None:
                    return callee.fn(self, args, this_binding)
                return callee.fn(self, args)
            except TypeError:
                return callee.fn(self, args)

        if isinstance(callee, JSFunction):
            return self._call_js_function(callee, args, this_val)

        if isinstance(callee, JSObject) and "Date" in str(callee):
            pass

        raise JSRuntimeError(f"'{callee}' is not a function")

    def _call_js_function(self, fn: JSFunction, args: List[Any], this_val: Any = None) -> Any:
        fn_env = Environment(fn.closure, is_function_scope=True)

        # Bind parameters
        rest_param = None
        regular_params = []
        for p in fn.params:
            if isinstance(p, ast.RestElement):
                rest_param = p.argument.name
            else:
                regular_params.append(p.name if isinstance(p, ast.Identifier) else p)

        for i, pname in enumerate(regular_params):
            val = args[i] if i < len(args) else UNDEFINED
            fn_env.define(pname, val, "var")

        if rest_param:
            rest_args = args[len(regular_params):]
            fn_env.define(rest_param, JSArray(rest_args), "var")

        try:
            if fn.is_arrow and not isinstance(fn.body, ast.BlockStatement):
                # Arrow function expression body
                prev = self.env
                self.env = fn_env
                try:
                    return self._evaluate(fn.body)
                finally:
                    self.env = prev
            else:
                self._hoist_declarations(fn.body.body, fn_env)
                self._execute_block(fn.body.body, fn_env)
                return UNDEFINED
        except ReturnSignal as rs:
            return rs.value

    def _eval_array(self, node: ast.ArrayExpression) -> JSArray:
        elements = []
        for el in node.elements:
            if el is None:
                continue
            if isinstance(el, ast.SpreadElement):
                spread_val = self._evaluate(el.argument)
                if isinstance(spread_val, JSArray):
                    elements.extend(spread_val.elements)
                else:
                    raise JSRuntimeError("Spread requires an array")
            else:
                elements.append(self._evaluate(el))
        return JSArray(elements)

    def _eval_object(self, node: ast.ObjectExpression) -> JSObject:
        obj = JSObject()
        for prop in node.properties:
            if prop.computed:
                key = to_string(self._evaluate(prop.key))
            elif isinstance(prop.key, ast.Identifier):
                key = prop.key.name
            elif isinstance(prop.key, ast.Literal):
                key = str(prop.key.value)
            else:
                key = to_string(self._evaluate(prop.key))
            obj.set(key, self._evaluate(prop.value))
        return obj


def interpret(source: str) -> List[str]:
    from project.lexer import Lexer
    from project.parser import Parser

    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interp = Interpreter()
    return interp.run(program)
