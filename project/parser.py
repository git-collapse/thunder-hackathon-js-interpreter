"""Recursive descent parser for JavaScript."""

from typing import List, Optional

from project.ast_nodes import (
    ArrayExpression,
    ArrowFunctionExpression,
    AssignmentExpression,
    BinaryExpression,
    BlockStatement,
    CallExpression,
    EmptyStatement,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    FunctionExpression,
    Identifier,
    IfStatement,
    Literal,
    LogicalExpression,
    MemberExpression,
    ObjectExpression,
    Program,
    Property,
    RestElement,
    ReturnStatement,
    SpreadElement,
    UnaryExpression,
    UpdateExpression,
    VariableDeclaration,
    VariableDeclarator,
    WhileStatement,
)
from project.errors import ParserError
from project.lexer import Lexer, Token, TokenType


class Parser:
    """Parse tokens into an AST."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        body = []
        while not self._is_at_end():
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        return Program(body=body)

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def _is_at_end(self) -> bool:
        return self._current().type == TokenType.EOF

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.pos += 1
        return self.tokens[self.pos - 1]

    def _check(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _match(self, *types: TokenType) -> bool:
        if self._check(*types):
            self._advance()
            return True
        return False

    def _expect(self, tt: TokenType, message: str) -> Token:
        if self._check(tt):
            return self._advance()
        tok = self._current()
        raise ParserError(message, tok.line, tok.column)

    def _parse_statement(self):
        if self._match(TokenType.FUNCTION):
            return self._parse_function_declaration()
        if self._match(TokenType.IF):
            return self._parse_if_statement()
        if self._match(TokenType.WHILE):
            return self._parse_while_statement()
        if self._match(TokenType.FOR):
            return self._parse_for_statement()
        if self._match(TokenType.RETURN):
            return self._parse_return_statement()
        if self._check(TokenType.LBRACE):
            return self._parse_block_statement()
        if self._check(TokenType.LET, TokenType.CONST, TokenType.VAR):
            return self._parse_variable_declaration()
        if self._match(TokenType.SEMICOLON):
            return EmptyStatement()

        expr = self._parse_expression()
        self._match(TokenType.SEMICOLON)
        return ExpressionStatement(expression=expr)

    def _parse_block_statement(self) -> BlockStatement:
        self._expect(TokenType.LBRACE, "Expected '{'")
        body = []
        while not self._check(TokenType.RBRACE) and not self._is_at_end():
            stmt = self._parse_statement()
            if stmt:
                body.append(stmt)
        self._expect(TokenType.RBRACE, "Expected '}'")
        return BlockStatement(body=body)

    def _parse_variable_declaration(self) -> VariableDeclaration:
        kind_tok = self._advance()
        kind = kind_tok.value
        declarations = [self._parse_variable_declarator()]
        while self._match(TokenType.COMMA):
            declarations.append(self._parse_variable_declarator())
        self._match(TokenType.SEMICOLON)
        return VariableDeclaration(kind=kind, declarations=declarations)

    def _parse_variable_declarator(self) -> VariableDeclarator:
        if self._check(TokenType.IDENTIFIER):
            id_node = Identifier(name=self._advance().value)
        else:
            raise ParserError("Expected identifier in variable declaration",
                              self._current().line, self._current().column)
        init = None
        if self._match(TokenType.EQ):
            init = self._parse_assignment_expression()
        return VariableDeclarator(id=id_node, init=init)

    def _parse_function_declaration(self) -> FunctionDeclaration:
        name = Identifier(name=self._expect(TokenType.IDENTIFIER, "Expected function name").value)
        self._expect(TokenType.LPAREN, "Expected '(' after function name")
        params = self._parse_params()
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        body = self._parse_block_statement()
        return FunctionDeclaration(id=name, params=params, body=body)

    def _parse_params(self) -> List:
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._parse_param())
            while self._match(TokenType.COMMA):
                params.append(self._parse_param())
        return params

    def _parse_param(self):
        if self._match(TokenType.SPREAD):
            arg = Identifier(name=self._expect(TokenType.IDENTIFIER, "Expected rest parameter name").value)
            return RestElement(argument=arg)
        return Identifier(name=self._expect(TokenType.IDENTIFIER, "Expected parameter name").value)

    def _parse_if_statement(self) -> IfStatement:
        self._expect(TokenType.LPAREN, "Expected '(' after 'if'")
        test = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after if condition")
        consequent = self._parse_statement()
        alternate = None
        if self._match(TokenType.ELSE):
            alternate = self._parse_statement()
        return IfStatement(test=test, consequent=consequent, alternate=alternate)

    def _parse_while_statement(self) -> WhileStatement:
        self._expect(TokenType.LPAREN, "Expected '(' after 'while'")
        test = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after while condition")
        body = self._parse_statement()
        return WhileStatement(test=test, body=body)

    def _parse_for_statement(self) -> ForStatement:
        self._expect(TokenType.LPAREN, "Expected '(' after 'for'")
        init = None
        if self._match(TokenType.SEMICOLON):
            pass
        elif self._check(TokenType.LET, TokenType.CONST, TokenType.VAR):
            init = self._parse_variable_declaration()
        else:
            init = self._parse_expression()
            self._expect(TokenType.SEMICOLON, "Expected ';' after for init")

        test = None
        if not self._check(TokenType.SEMICOLON):
            test = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "Expected ';' after for condition")

        update = None
        if not self._check(TokenType.RPAREN):
            update = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after for clauses")

        body = self._parse_statement()
        return ForStatement(init=init, test=test, update=update, body=body)

    def _parse_return_statement(self) -> ReturnStatement:
        argument = None
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE) and not self._is_at_end():
            argument = self._parse_expression()
        self._match(TokenType.SEMICOLON)
        return ReturnStatement(argument=argument)

    def _parse_expression(self):
        return self._parse_assignment_expression()

    def _parse_assignment_expression(self):
        expr = self._parse_conditional_expression()

        assign_ops = {
            TokenType.EQ: "=",
            TokenType.PLUS_EQ: "+=",
            TokenType.MINUS_EQ: "-=",
            TokenType.STAR_EQ: "*=",
            TokenType.SLASH_EQ: "/=",
            TokenType.PERCENT_EQ: "%=",
        }
        for tt, op in assign_ops.items():
            if self._match(tt):
                right = self._parse_assignment_expression()
                return AssignmentExpression(operator=op, left=expr, right=right)
        return expr

    def _parse_conditional_expression(self):
        return self._parse_logical_or_expression()

    def _parse_logical_or_expression(self):
        expr = self._parse_logical_and_expression()
        while self._match(TokenType.PIPE_PIPE):
            right = self._parse_logical_and_expression()
            expr = LogicalExpression(operator="||", left=expr, right=right)
        return expr

    def _parse_logical_and_expression(self):
        expr = self._parse_equality_expression()
        while self._match(TokenType.AMP_AMP):
            right = self._parse_equality_expression()
            expr = LogicalExpression(operator="&&", left=expr, right=right)
        return expr

    def _parse_equality_expression(self):
        ops = {
            TokenType.EQ_EQ: "==",
            TokenType.EQ_EQ_EQ: "===",
            TokenType.BANG_EQ: "!=",
            TokenType.BANG_EQ_EQ: "!==",
        }
        expr = self._parse_relational_expression()
        while True:
            matched = False
            for tt, op in ops.items():
                if self._match(tt):
                    right = self._parse_relational_expression()
                    expr = BinaryExpression(operator=op, left=expr, right=right)
                    matched = True
                    break
            if not matched:
                break
        return expr

    def _parse_relational_expression(self):
        ops = {
            TokenType.LT: "<",
            TokenType.LT_EQ: "<=",
            TokenType.GT: ">",
            TokenType.GT_EQ: ">=",
        }
        expr = self._parse_additive_expression()
        while True:
            matched = False
            for tt, op in ops.items():
                if self._match(tt):
                    right = self._parse_additive_expression()
                    expr = BinaryExpression(operator=op, left=expr, right=right)
                    matched = True
                    break
            if not matched:
                break
        return expr

    def _parse_additive_expression(self):
        expr = self._parse_multiplicative_expression()
        while True:
            if self._match(TokenType.PLUS):
                right = self._parse_multiplicative_expression()
                expr = BinaryExpression(operator="+", left=expr, right=right)
            elif self._match(TokenType.MINUS):
                right = self._parse_multiplicative_expression()
                expr = BinaryExpression(operator="-", left=expr, right=right)
            else:
                break
        return expr

    def _parse_multiplicative_expression(self):
        expr = self._parse_power_expression()
        while True:
            if self._match(TokenType.STAR):
                right = self._parse_power_expression()
                expr = BinaryExpression(operator="*", left=expr, right=right)
            elif self._match(TokenType.SLASH):
                right = self._parse_power_expression()
                expr = BinaryExpression(operator="/", left=expr, right=right)
            elif self._match(TokenType.PERCENT):
                right = self._parse_power_expression()
                expr = BinaryExpression(operator="%", left=expr, right=right)
            else:
                break
        return expr

    def _parse_power_expression(self):
        expr = self._parse_unary_expression()
        if self._match(TokenType.STAR_STAR):
            right = self._parse_power_expression()
            expr = BinaryExpression(operator="**", left=expr, right=right)
        return expr

    def _parse_unary_expression(self):
        if self._match(TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            op = self.tokens[self.pos - 1].value
            arg = self._parse_unary_expression()
            return UpdateExpression(operator=op, argument=arg, prefix=True)
        if self._match(TokenType.BANG):
            return UnaryExpression(operator="!", argument=self._parse_unary_expression())
        if self._match(TokenType.MINUS):
            return UnaryExpression(operator="-", argument=self._parse_unary_expression())
        if self._match(TokenType.PLUS):
            return UnaryExpression(operator="+", argument=self._parse_unary_expression())
        return self._parse_postfix_expression()

    def _parse_postfix_expression(self):
        expr = self._parse_call_expression()
        if self._match(TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            op = self.tokens[self.pos - 1].value
            return UpdateExpression(operator=op, argument=expr, prefix=False)
        return expr

    def _parse_call_expression(self):
        expr = self._parse_primary_expression()
        while True:
            if self._match(TokenType.LPAREN):
                args = self._parse_arguments()
                self._expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpression(callee=expr, arguments=args)
            elif self._match(TokenType.LBRACKET):
                prop = self._parse_expression()
                self._expect(TokenType.RBRACKET, "Expected ']' after computed member")
                expr = MemberExpression(object=expr, property=prop, computed=True)
            elif self._match(TokenType.DOT):
                name = self._expect(TokenType.IDENTIFIER, "Expected property name").value
                expr = MemberExpression(
                    object=expr,
                    property=Identifier(name=name),
                    computed=False,
                )
            else:
                break
        return expr

    def _parse_arguments(self) -> List:
        args = []
        if not self._check(TokenType.RPAREN):
            args.append(self._parse_assignment_expression())
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RPAREN):
                    break
                args.append(self._parse_assignment_expression())
        return args

    def _parse_primary_expression(self):
        if self._match(TokenType.TRUE):
            return Literal(value=True)
        if self._match(TokenType.FALSE):
            return Literal(value=False)
        if self._match(TokenType.NULL):
            return Literal(value=None)
        if self._match(TokenType.UNDEFINED):
            return Literal(value="undefined")
        if self._match(TokenType.NUMBER):
            return Literal(value=self.tokens[self.pos - 1].value)
        if self._match(TokenType.STRING):
            return Literal(value=self.tokens[self.pos - 1].value)
        if self._match(TokenType.IDENTIFIER):
            name = self.tokens[self.pos - 1].value
            if self._check(TokenType.ARROW):
                self._advance()  # consume =>
                body = self._parse_arrow_body()
                return ArrowFunctionExpression(
                    params=[Identifier(name=name)], body=body
                )
            return Identifier(name=name)
        if self._check(TokenType.LPAREN) and self._could_be_arrow_function():
            self._advance()
            params = self._parse_arrow_params_from_paren()
            self._expect(TokenType.ARROW, "Expected '=>'")
            body = self._parse_arrow_body()
            return ArrowFunctionExpression(params=params, body=body)
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        if self._match(TokenType.LBRACKET):
            return self._parse_array_expression()
        if self._match(TokenType.LBRACE):
            return self._parse_object_expression()
        if self._match(TokenType.NEW):
            return self._parse_new_expression()
        if self._match(TokenType.FUNCTION):
            return self._parse_function_expression()
        tok = self._current()
        raise ParserError(f"Unexpected token {tok.type.name}", tok.line, tok.column)

    def _could_be_arrow_function(self) -> bool:
        """Heuristic: (a, b) => or (a) => or () =>"""
        depth = 0
        i = self.pos
        while i < len(self.tokens):
            t = self.tokens[i]
            if t.type == TokenType.LPAREN:
                depth += 1
            elif t.type == TokenType.RPAREN:
                depth -= 1
                if depth == 0:
                    nxt = self.tokens[i + 1] if i + 1 < len(self.tokens) else None
                    return nxt is not None and nxt.type == TokenType.ARROW
            elif t.type in (TokenType.LBRACE, TokenType.RBRACE):
                return False
            i += 1
        return False

    def _parse_arrow_params_from_paren(self) -> List:
        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._parse_param())
            while self._match(TokenType.COMMA):
                params.append(self._parse_param())
        self._expect(TokenType.RPAREN, "Expected ')' after arrow function params")
        return params

    def _parse_arrow_body(self):
        if self._check(TokenType.LBRACE):
            return self._parse_block_statement()
        return self._parse_assignment_expression()

    def _parse_new_expression(self):
        callee = self._parse_primary_expression()
        if self._match(TokenType.LPAREN):
            args = self._parse_arguments()
            self._expect(TokenType.RPAREN, "Expected ')' after constructor arguments")
            return CallExpression(callee=callee, arguments=args)
        return CallExpression(callee=callee, arguments=[])

    def _parse_function_expression(self) -> FunctionExpression:
        name = None
        if self._check(TokenType.IDENTIFIER):
            name = Identifier(name=self._advance().value)
        self._expect(TokenType.LPAREN, "Expected '(' after 'function'")
        params = self._parse_params()
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        body = self._parse_block_statement()
        return FunctionExpression(id=name, params=params, body=body)

    def _parse_array_expression(self) -> ArrayExpression:
        elements = []
        if not self._check(TokenType.RBRACKET):
            if self._match(TokenType.SPREAD):
                elements.append(SpreadElement(argument=self._parse_assignment_expression()))
            else:
                elements.append(self._parse_assignment_expression())
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RBRACKET):
                    elements.append(None)  # trailing comma
                    break
                if self._match(TokenType.SPREAD):
                    elements.append(SpreadElement(argument=self._parse_assignment_expression()))
                else:
                    elements.append(self._parse_assignment_expression())
        self._expect(TokenType.RBRACKET, "Expected ']' after array elements")
        return ArrayExpression(elements=elements)

    def _parse_object_expression(self) -> ObjectExpression:
        properties = []
        if not self._check(TokenType.RBRACE):
            properties.append(self._parse_property())
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RBRACE):
                    break
                properties.append(self._parse_property())
        self._expect(TokenType.RBRACE, "Expected '}' after object properties")
        return ObjectExpression(properties=properties)

    def _parse_property(self) -> Property:
        computed = False
        if self._match(TokenType.LBRACKET):
            key = self._parse_expression()
            self._expect(TokenType.RBRACKET, "Expected ']' after computed key")
            computed = True
        elif self._check(TokenType.STRING, TokenType.IDENTIFIER):
            key = Literal(value=self._advance().value)
        elif self._check(TokenType.NUMBER):
            key = Literal(value=str(self._advance().value))
        else:
            raise ParserError("Expected property key", self._current().line, self._current().column)
        self._expect(TokenType.COLON, "Expected ':' after property key")
        value = self._parse_assignment_expression()
        return Property(key=key, value=value, computed=computed)


def parse(source: str) -> Program:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()
