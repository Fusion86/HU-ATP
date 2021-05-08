import os
import re
import json
import types
from enum import Enum, unique
from functools import reduce
from typing import List, Tuple, Union, Iterable, Type
from pprint import pprint
from smickelscript import lexer


class ParserException(Exception):
    pass


class UnexpectedTokenException(ParserException):
    pass


class UnexpectedKeywordException(ParserException):
    pass


class ParserJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return {"__type": type(o).__name__, **o.__dict__}


class ParserToken:
    def __repr__(self):
        return "<{}>".format(type(self).__name__)

    def __eq__(self, value):
        if hasattr(self, "__dict__") and hasattr(value, "__dict__"):
            return vars(self) == vars(value)
        return super().__eq__(value)


class FuncParameterToken(ParserToken):
    def __init__(self, identifier, _type):
        self.identifier = identifier
        self.variable_type = _type


# class ArgumentToken(ParserToken):
#     def __init__(self, value):
#         self.value = value


class LiteralToken(ParserToken):
    def __init__(self, value):
        self.value = value


class FuncCallToken(ParserToken):
    def __init__(self, identifier: lexer.IdentifierToken, args: List = None):
        self.identifier = identifier
        self.args = args or []


class OperatorToken(ParserToken):
    def __init__(self, lhs, operator, rhs):
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs


# class ConditionToken(OperatorToken):
#     def __init__(self, lhs, operator, rhs):
#         self.lhs = lhs
#         self.operator = operator
#         self.rhs = rhs


# class ArithmeticToken(OperatorToken):
#     def __init__(self, lhs, operator, rhs):
#         self.lhs = lhs
#         self.operator = operator
#         self.rhs = rhs


class IfStatementToken(ParserToken):
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition
        self.true_body = true_body
        self.false_body = false_body


class WhileStatementToken(ParserToken):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body


class FunctionToken(ParserToken):
    def __init__(self, identifier, parameters, return_type, body):
        self.identifier = identifier
        self.parameters = parameters
        self.return_type = return_type
        self.body = body


class ReturnToken(ParserToken):
    def __init__(self, value):
        self.value = value


class UnsetValueToken(ParserToken):
    pass


class InitVariableToken(ParserToken):
    def __init__(self, identifier, _type, value):
        self.identifier = identifier
        self.variable_type = _type
        self.value = value


class AssignVariableToken(ParserToken):
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value


# TODO: Find a better name for this
class ScopeWithBody(ParserToken):
    def __init__(self, body):
        self.body = body


def load_file(filename: str):
    with open(filename) as f:
        tokens = lexer.tokenize_file(filename)
        ast = parse_tokens(tokens)
        return ast


def load_source(source: str):
    tokens = lexer.tokenize_str(source)
    ast = parse_tokens(tokens)
    return ast


def parse_tokens(tokens: List[lexer.LexerToken], until_token_of_type=None):
    if len(tokens) == 0:
        return []

    # if until_token_of_type and type(tokens[0]) == until_token_of_type:
    #     return tokens

    ast, tokens = parse_statement(tokens)

    if len(tokens) > 0:
        return [ast] + parse_tokens(tokens, until_token_of_type)
    else:
        return [ast]


def parse_scope(tokens: List[lexer.LexerToken], statements=None):
    if statements == None:
        statements = []
        _, tokens = eat_one(tokens, lexer.ScopeOpenToken)

    end_scope_token, tokens = eat_one(tokens, lexer.ScopeCloseToken, False)
    if end_scope_token:
        return ScopeWithBody(statements), tokens
    else:
        token, tokens = parse_statement(tokens)

        # # Not every statement needs to end with a semicolon.
        # if type(token) not in no_semicolon_after_these:
        #     _, tokens = eat_one(tokens, lexer.SemiToken)
        return parse_scope(tokens, statements + [token])


def parse_statement(tokens: List[lexer.LexerToken]):
    token_type = type(tokens[0])
    if token_type in token_parsers:
        ast, tokens = token_parsers[token_type](tokens)

        # TODO: Not every statement needs to end with a semicolon.
        _, tokens = eat_one(tokens, lexer.SemiToken, False)

        return ast, tokens
    else:
        raise UnexpectedTokenException(
            "Error on line {}. Unexpected token '{}'.".format(
                tokens[0].line_nr, token_type.__name__
            )
        )


def parse_keyword_token(tokens: List[lexer.LexerToken]):
    assert type(tokens[0]) == lexer.KeywordToken

    keyword = tokens[0].value
    if keyword in keyword_parsers:
        return keyword_parsers[keyword](tokens)
    else:
        raise UnexpectedKeywordException(
            "Error on line {}. Unexpected keyword '{}'.".format(tokens[0].line_nr, keyword)
        )


# TODO: Rename this?
def parse_identifier_action(tokens: List[lexer.LexerToken]):
    token, tokens = eat_one(tokens, lexer.ValueToken)

    # What do we do with this identifier?

    # Is it a function call?
    if type(tokens[0]) == lexer.ArgumentsOpenToken:
        args, tokens = parse_arguments(tokens)
        token = FuncCallToken(token, args)

    # Is it a variable assignment?
    elif type(tokens[0]) == lexer.AssignmentToken:
        _, tokens = eat_one(tokens, lexer.AssignmentToken)
        statement, tokens = parse_identifier_action(tokens)
        token = AssignVariableToken(token, statement)

    # Is it a comparison?
    # TODO: This shouldn't be here, this is already covered in the `parse_condition` function.
    # elif isinstance(tokens[0], lexer.ComparisonToken):
    #     # lhs = token
    #     operator, tokens = eat_one(tokens, lexer.ComparisonToken)
    #     rhs, tokens = parse_statement(tokens)
    #     token = ConditionToken(token, operator, rhs)
    #     raise Exception()

    # Is the next token an operator.
    elif isinstance(tokens[0], lexer.OperatorToken):
        operator, tokens = eat_one(tokens, lexer.OperatorToken)
        rhs, tokens = parse_statement(tokens)
        token = OperatorToken(token, operator, rhs)

    # Is this just a ValueLiteral?
    if isinstance(token, lexer.LiteralToken):
        return LiteralToken(token), tokens

    # All statements should end with a semicolon.
    # _, tokens = eat_one(tokens, lexer.SemiToken)
    return token, tokens


def parse_if_statement(tokens):
    # Parse if statement
    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="if")
    condition, tokens = parse_condition(tokens)
    true_body, tokens = parse_scope(tokens)

    # Parse else statement, if it exists
    else_token, tokens = eat_one(tokens, lexer.KeywordToken, False, "else")
    if else_token:
        raise NotImplementedError("'else' keywords are currently not implemented.")

    return IfStatementToken(condition, true_body), tokens


def parse_condition(tokens):
    _, tokens = eat_one(tokens, lexer.ArgumentsOpenToken)
    # lhs, tokens = parse_statement(tokens)
    # operator, tokens = eat_one(tokens, lexer.ComparisonToken)
    # rhs, tokens = parse_statement(tokens)
    condition, tokens = parse_statement(tokens)
    _, tokens = eat_one(tokens, lexer.ArgumentsCloseToken)
    return condition, tokens


def parse_var(tokens):
    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="var")
    identifier, tokens = eat_one(tokens, lexer.IdentifierToken)
    type_token, tokens = parse_typehint(tokens)

    # Assignment is optional
    op, tokens = eat_one(tokens, lexer.AssignmentToken, False)
    if op:
        value, tokens = parse_statement(tokens)
    else:
        value = UnsetValueToken()

    return InitVariableToken(identifier, type_token, value), tokens


def parse_while(tokens):
    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="while")
    condition, tokens = parse_condition(tokens)
    body, tokens = parse_scope(tokens)
    return WhileStatementToken(condition, body), tokens


# def parse_literal(tokens):
#     return LiteralToken(tokens[0]), tokens[1:]


def parse_comment(tokens):
    return tokens[0], tokens[1:]


def parse_func(tokens):
    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="func")
    identifier, tokens = eat_one(tokens, lexer.IdentifierToken)
    parameters, tokens = parse_parameters(tokens)
    type_token, tokens = parse_typehint(tokens, default="void")
    body, tokens = parse_scope(tokens)

    return FunctionToken(identifier, parameters, type_token, body), tokens


def parse_return(tokens):
    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="return")
    retval, tokens = parse_statement(tokens)
    return ReturnToken(retval), tokens


def parse_typehint(tokens, required=False, default=None):
    typehint_token, tokens = eat_one(tokens, lexer.TypehintToken, False)
    if typehint_token:
        return eat_one(tokens, lexer.TypeToken)
    elif required:
        raise ParserException(
            "Error on line {}. A typehint is required, but not found.".format(tokens[0].line_nr)
        )
    else:
        return lexer.TypeToken(tokens[0].line_nr, default), tokens


def parse_bool_literal(tokens):
    # # It is either true (optional)
    # true_or_false, tokens = eat_one(tokens, lexer.KeywordToken)
    # if true_or_false.value in ["true", "false"]:
    #     return LiteralToken(true_or_false), tokens
    # # This should never happen, but just to be safe.
    # raise Exception("Invalid boolean token '{}'".format(true_or_false))

    # It is either true (optional)
    true, tokens = eat_one(tokens, lexer.KeywordToken, False, "true")
    if true:
        return LiteralToken(true), tokens

    # Or false (required, because if it would be true we would've returned already)
    false, tokens = eat_one(tokens, lexer.KeywordToken, with_value="false")
    return LiteralToken(false), tokens


def parse_parameters(tokens, params=None):
    if params == None:
        _, tokens = eat_one(tokens, lexer.ArgumentsOpenToken)
        params = []

    if type(tokens[0]) == lexer.ArgumentsCloseToken:
        return params, tokens[1:]

    identifier, tokens = eat_one(tokens, lexer.IdentifierToken)
    type_token, tokens = parse_typehint(tokens)
    return parse_parameters(tokens, params + [FuncParameterToken(identifier, type_token)])


def parse_arguments(tokens, args=None):
    if args == None:
        _, tokens = eat_one(tokens, lexer.ArgumentsOpenToken)
        args = []

    if type(tokens[0]) == lexer.ArgumentsCloseToken:
        return args, tokens[1:]

    statement, tokens = parse_statement(tokens)
    # return parse_arguments(tokens, args + [ArgumentToken(statement)])
    return parse_arguments(tokens, args + [statement])


def eat_one(tokens, of_type: Type, required=True, with_value=None):
    if len(tokens) > 0 and isinstance(tokens[0], of_type):
        if with_value and tokens[0].value != with_value:
            if required:
                raise UnexpectedTokenException(
                    "Error on line {}. Expected a token with value '{}', but found a token with value '{}'.".format(
                        tokens[0].line_nr, with_value, tokens[0].value
                    )
                )
            return None, tokens
        return tokens[0], tokens[1:]
    if required:
        raise UnexpectedTokenException(
            "Error on line {}. Expected token of type '{}', but found a token of type '{}'.".format(
                tokens[0].line_nr, of_type.__name__, type(tokens[0]).__name__
            )
        )
    return None, tokens


token_parsers = {
    lexer.KeywordToken: parse_keyword_token,
    lexer.IdentifierToken: parse_identifier_action,
    lexer.StringLiteralToken: parse_identifier_action,
    lexer.NumberLiteralToken: parse_identifier_action,
    lexer.BoolLiteralToken: parse_identifier_action,
    lexer.CommentToken: parse_comment,
    lexer.ScopeOpenToken: parse_scope,
}

keyword_parsers = {
    "if": parse_if_statement,
    # "else": None,
    "func": parse_func,
    "return": parse_return,
    "true": parse_bool_literal,
    "false": parse_bool_literal,
    "var": parse_var,
    "while": parse_while,
}

# no_semicolon_after_these = [IfStatementToken, WhileStatementToken, lexer.CommentToken]


def print_ast(ast):
    print(json.dumps(ast, indent=4, cls=ParserJsonEncoder))


if __name__ == "__main__":

    def print_parsed_file(filename: str):
        tokens = lexer.tokenize_file(filename)
        ast = parse_tokens(tokens)
        print("Printing AST for {}".format(filename))
        print_ast(ast)
        print()

    [print_parsed_file("../example/" + file) for file in os.listdir("../example")]
