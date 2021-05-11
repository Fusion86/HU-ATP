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
    def __init__(self, identifier: lexer.IdentifierToken, _type: lexer.TypeToken):
        self.identifier = identifier
        self.variable_type = _type


class LiteralToken(ParserToken):
    def __init__(self, value: lexer.ValueToken):
        self.value = value


class FuncCallToken(ParserToken):
    def __init__(self, identifier: lexer.IdentifierToken, args: List = None):
        self.identifier = identifier
        self.args = args or []


class OperatorToken(ParserToken):
    def __init__(self, lhs: ParserToken, operator: ParserToken, rhs: ParserToken):
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs


class ScopeWithBody(ParserToken):
    def __init__(self, body: List[ParserToken]):
        self.body = body


class IfStatementToken(ParserToken):
    def __init__(
        self, condition: ParserToken, true_body: ScopeWithBody, false_body: ScopeWithBody = None
    ):
        self.condition = condition
        self.true_body = true_body
        self.false_body = false_body


class WhileStatementToken(ParserToken):
    def __init__(self, condition: ParserToken, body: ScopeWithBody):
        self.condition = condition
        self.body = body


class FunctionToken(ParserToken):
    def __init__(
        self,
        identifier: lexer.IdentifierToken,
        parameters: List[FuncParameterToken],
        return_type: lexer.TypeToken,
        body: ScopeWithBody,
    ):
        self.identifier = identifier
        self.parameters = parameters
        self.return_type = return_type
        self.body = body


class ReturnToken(ParserToken):
    def __init__(self, value: ParserToken):
        self.value = value


class UnsetValueToken(ParserToken):
    """Used for variable initializations where no value is given."""

    pass


class InitVariableToken(ParserToken):
    def __init__(self, identifier: lexer.IdentifierToken, _type: lexer.TypeToken, value):
        self.identifier = identifier
        self.variable_type = _type
        self.value = value


class AssignVariableToken(ParserToken):
    def __init__(self, identifier: lexer.IdentifierToken, value):
        self.identifier = identifier
        self.value = value


def load_file(filename: str) -> List[ParserToken]:
    """Load a SmickelScript source file and parse it.

    Args:
        filename (str): The filename of the source file.

    Returns:
        List[ParserToken]: Abstract Syntax Tree.
    """

    tokens = lexer.tokenize_file(filename)
    ast = parse_tokens(tokens)
    return ast


def load_source(source: str) -> List[ParserToken]:
    """Load a SmickelScript source string and parse it.

    Args:
        source (str): SmickelScript source code.

    Returns:
        List[ParserToken]: Abstract Syntax Tree.
    """

    tokens = lexer.tokenize_str(source)
    ast = parse_tokens(tokens)
    return ast


def parse_tokens(tokens: List[lexer.LexerToken]) -> List[ParserToken]:
    """Parse a list of LexerTokens and return an AST.

    Args:
        tokens (List[lexer.LexerToken]): List of the LexerTokens, obtained by calling lexer.tokenize, tokenize_str or tokenize_file.

    Returns:
        List[ParserToken]: Abstract Syntax Tree.
    """

    if len(tokens) == 0:
        return []

    ast, tokens = parse_token(tokens)

    if len(tokens) > 0:
        return [ast] + parse_tokens(tokens)
    else:
        return [ast]


def parse_scope(
    tokens: List[lexer.LexerToken], statements: List[ParserToken] = None
) -> Tuple[ScopeWithBody, List[lexer.LexerToken]]:
    """Parse a list of LexerTokens until the end of the scope and return an AST.

    Args:
        tokens (List[lexer.LexerToken]):
        statements (List[ParserToken], optional): List of statements already in this scope. Defaults to None.

    Returns:
        Tuple[ScopeWithBody, List[lexer.LexerToken]]: A tuple with a token representing the parsed scope, and the rest of the tokens that still need to be parsed.
    """

    if statements == None:
        statements = []
        _, tokens = eat_one(tokens, lexer.ScopeOpenToken)

    end_scope_token, tokens = eat_one(tokens, lexer.ScopeCloseToken, False)
    if end_scope_token:
        return ScopeWithBody(statements), tokens
    else:
        token, tokens = parse_token(tokens)

        # # Not every statement needs to end with a semicolon.
        # if type(token) not in no_semicolon_after_these:
        #     _, tokens = eat_one(tokens, lexer.SemiToken)
        return parse_scope(tokens, statements + [token])


def parse_token(tokens: List[lexer.LexerToken]) -> Tuple[ParserToken, List[lexer.LexerToken]]:
    """Parse one or multiple LexerTokens into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Raises:
        UnexpectedTokenException: When an unexpected token is found. This usually happens when the source code is invalid.

    Returns:
        Tuple[ParserToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

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


def parse_keyword_token(
    tokens: List[lexer.LexerToken],
) -> Tuple[ParserToken, List[lexer.LexerToken]]:
    """Parse a lexer.KeywordToken into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Raises:
        UnexpectedKeywordException: [description]

    Returns:
        Tuple[ParserToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    assert type(tokens[0]) == lexer.KeywordToken

    keyword = tokens[0].value
    if keyword in keyword_parsers:
        return keyword_parsers[keyword](tokens)
    else:
        raise UnexpectedKeywordException(
            "Error on line {}. Unexpected keyword '{}'.".format(tokens[0].line_nr, keyword)
        )


# TODO: Rename this?
def parse_identifier_action(
    tokens: List[lexer.LexerToken],
) -> Tuple[ParserToken, List[lexer.LexerToken]]:
    """Parse an identifier, possibly with a matching action.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[ParserToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

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
        rhs, tokens = parse_token(tokens)
        token = OperatorToken(token, operator, rhs)

    # Is this just a ValueLiteral?
    if isinstance(token, lexer.LiteralToken):
        return LiteralToken(token), tokens

    return token, tokens


def parse_if_statement(
    tokens: List[lexer.LexerToken],
) -> Tuple[IfStatementToken, List[lexer.LexerToken]]:
    """Parse an if statement into a ParsedToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Raises:
        NotImplementedError: [description]

    Returns:
        Tuple[IfStatementToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    # Parse if statement
    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="if")
    condition, tokens = parse_condition(tokens)
    true_body, tokens = parse_scope(tokens)

    # Parse else statement, if it exists
    else_token, tokens = eat_one(tokens, lexer.KeywordToken, False, "else")
    if else_token:
        raise NotImplementedError("'else' keywords are currently not implemented.")

    return IfStatementToken(condition, true_body), tokens


def parse_condition(tokens: List[lexer.LexerToken]) -> Tuple[ParserToken, List[lexer.LexerToken]]:
    """Parse a condition into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[ParserToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    _, tokens = eat_one(tokens, lexer.ArgumentsOpenToken)
    condition, tokens = parse_token(tokens)
    _, tokens = eat_one(tokens, lexer.ArgumentsCloseToken)
    return condition, tokens


def parse_var(tokens: List[lexer.LexerToken]) -> Tuple[InitVariableToken, List[lexer.LexerToken]]:
    """Parse a variable initialization token into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[InitVariableToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="var")
    identifier, tokens = eat_one(tokens, lexer.IdentifierToken)
    type_token, tokens = parse_typehint(tokens)

    # Assignment is optional
    op, tokens = eat_one(tokens, lexer.AssignmentToken, False)
    if op:
        value, tokens = parse_token(tokens)
    else:
        value = UnsetValueToken()

    return InitVariableToken(identifier, type_token, value), tokens


def parse_while(
    tokens: List[lexer.LexerToken],
) -> Tuple[WhileStatementToken, List[lexer.LexerToken]]:
    """Parse a while loop into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[WhileStatementToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="while")
    condition, tokens = parse_condition(tokens)
    body, tokens = parse_scope(tokens)
    return WhileStatementToken(condition, body), tokens


def parse_comment(
    tokens: List[lexer.LexerToken],
) -> Tuple[lexer.CommentToken, List[lexer.LexerToken]]:
    """This function doesn't do anything. It just returns the lexer.CommentToken and pops the first item from the tokens list.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[lexer.CommentToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    return tokens[0], tokens[1:]


def parse_func(tokens: List[lexer.LexerToken]) -> Tuple[FunctionToken, List[lexer.LexerToken]]:
    """Parse a function with its body into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[FunctionToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="func")
    identifier, tokens = eat_one(tokens, lexer.IdentifierToken)
    parameters, tokens = parse_parameters(tokens)
    type_token, tokens = parse_typehint(tokens, default="void")
    body, tokens = parse_scope(tokens)

    return FunctionToken(identifier, parameters, type_token, body), tokens


def parse_return(tokens: List[lexer.LexerToken]) -> Tuple[ReturnToken, List[lexer.LexerToken]]:
    """Parse a return statement into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[ReturnToken, List[lexer.LexerToken]]:A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    _, tokens = eat_one(tokens, lexer.KeywordToken, with_value="return")
    retval, tokens = parse_token(tokens)
    return ReturnToken(retval), tokens


def parse_typehint(
    tokens: List[lexer.LexerToken], required=False, default=None
) -> Tuple[lexer.TypeToken, List[lexer.LexerToken]]:
    """Parse a TypeHint into a TypeToken.

    Args:
        tokens (List[lexer.LexerToken]):
        required (bool, optional): Typehints usually aren't required. Pass true to throw an error when no TypeHint is found.. Defaults to False.
        default ([type], optional): The default type, when no TypeHint is found. Defaults to None.

    Raises:
        ParserException: Thrown when a required TypeHint is missing.

    Returns:
        Tuple[lexer.TypeToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    typehint_token, tokens = eat_one(tokens, lexer.TypehintToken, False)
    if typehint_token:
        return eat_one(tokens, lexer.TypeToken)
    elif required:
        raise ParserException(
            "Error on line {}. A typehint is required, but not found.".format(tokens[0].line_nr)
        )
    else:
        return lexer.TypeToken(tokens[0].line_nr, default), tokens


def parse_bool_literal(
    tokens: List[lexer.LexerToken],
) -> Tuple[LiteralToken, List[lexer.LexerToken]]:
    """Parse a bool literal into a ParserToken.

    Args:
        tokens (List[lexer.LexerToken]):

    Returns:
        Tuple[LiteralToken, List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    # It is either true (optional)
    true, tokens = eat_one(tokens, lexer.KeywordToken, False, "true")
    if true:
        return LiteralToken(true), tokens

    # Or false (required, because if it would be true we would've returned already)
    false, tokens = eat_one(tokens, lexer.KeywordToken, with_value="false")
    return LiteralToken(false), tokens


def parse_parameters(
    tokens: List[lexer.LexerToken], params=None
) -> Tuple[List[FuncParameterToken], List[lexer.LexerToken]]:
    """Parse one or multiple parameters.

    Args:
        tokens (List[lexer.LexerToken]):
        params ([type], optional): Existing parameters, used for recursion. Defaults to None.

    Returns:
        Tuple[List[FuncParameterToken], List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    if params == None:
        _, tokens = eat_one(tokens, lexer.ArgumentsOpenToken)
        params = []

    if type(tokens[0]) == lexer.ArgumentsCloseToken:
        return params, tokens[1:]

    identifier, tokens = eat_one(tokens, lexer.IdentifierToken)
    type_token, tokens = parse_typehint(tokens)
    arg_separator, tokens = eat_one(tokens, lexer.ArgumentSeparatorToken, False)
    return parse_parameters(tokens, params + [FuncParameterToken(identifier, type_token)])


def parse_arguments(
    tokens: List[lexer.LexerToken], args=None
) -> Tuple[List[ParserToken], List[lexer.LexerToken]]:
    """Parse one or multiple arguments.

    Args:
        tokens (List[lexer.LexerToken]):
        args ([type], optional): Existing arguments, used for recursion. Defaults to None.

    Returns:
        Tuple[List[ParserToken], List[lexer.LexerToken]]: A tuple with the parsed token, and the rest of the tokens that still need to be parsed.
    """

    if args == None:
        _, tokens = eat_one(tokens, lexer.ArgumentsOpenToken)
        args = []

    if type(tokens[0]) == lexer.ArgumentsCloseToken:
        return args, tokens[1:]

    statement, tokens = parse_token(tokens)
    arg_separator, tokens = eat_one(tokens, lexer.ArgumentSeparatorToken, False)
    return parse_arguments(tokens, args + [statement])


def eat_one(
    tokens: List[lexer.LexerToken], of_type: Type, required=True, with_value=None
) -> Tuple[ParserToken, List[lexer.LexerToken]]:
    """Eat one token from the stream.

    Args:
        tokens (List[lexer.LexerToken]):
        of_type (Type): The type of the token to eat.
        required (bool, optional): True when the token is required. Defaults to True.
        with_value ([type], optional): The expected value of the token. Defaults to None.

    Raises:
        UnexpectedTokenException: When a required token 'of_type' is not found.
        UnexpectedTokenException: When a required token has the wrong value.

    Returns:
        Tuple[ParserToken, List[lexer.LexerToken]]: [description]
    """

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


def print_ast(ast: List[ParserToken]):
    print(json.dumps(ast, indent=4, cls=ParserJsonEncoder))


if __name__ == "__main__":

    def print_parsed_file(filename: str):
        tokens = lexer.tokenize_file(filename)
        ast = parse_tokens(tokens)
        print("Printing AST for {}".format(filename))
        print_ast(ast)
        print()

    [print_parsed_file("../example/" + file) for file in os.listdir("../example")]
