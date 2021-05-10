import os
import re
import json
import types
import itertools
from enum import Enum, unique
from functools import reduce
from typing import List, Tuple, Union, Iterable
from pprint import pprint


class LexerException(Exception):
    pass


class UnexpectedCharacterException(LexerException):
    pass


class LexerJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return {"__type": type(o).__name__, **o.__dict__}


class LexerToken:
    def __init__(self, line_nr: int):
        self.line_nr = line_nr

    def __repr__(self):
        return "<{}>".format(type(self).__name__)

    def __eq__(self, value):
        if hasattr(self, "__dict__") and hasattr(value, "__dict__"):
            return vars(self) == vars(value)
        return super().__eq__(value)


class KeywordToken(LexerToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr)
        self.value = value

    def __repr__(self):
        return "<KeywordToken value: {}>".format(self.value)


class TypeToken(LexerToken):
    def __init__(self, line_nr: int, type_name):
        super().__init__(line_nr)
        self.type_name = type_name


class ValueToken(LexerToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr)
        self.value = value


class IdentifierToken(ValueToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr, value)


class LiteralToken(ValueToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr, value)
        self.value = value


class StringLiteralToken(LiteralToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr, value)


class NumberLiteralToken(LiteralToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr, value)


class BoolLiteralToken(LiteralToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr, value)


class CommentToken(LexerToken):
    def __init__(self, line_nr: int, value: str):
        super().__init__(line_nr)
        self.value = value


class ScopeOpenToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class ScopeCloseToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class ArgumentsOpenToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class ArgumentsCloseToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class TypehintToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class SemiToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class ArgumentSeparatorToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class OperatorToken(LexerToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class ArithmeticToken(OperatorToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class AdditionToken(ArithmeticToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class SubtractionToken(ArithmeticToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class MultiplicationToken(ArithmeticToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class AssignmentToken(OperatorToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class ComparisonToken(OperatorToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class EqualToken(ComparisonToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class NotEqualToken(ComparisonToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class GreaterThanToken(ComparisonToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class SmallerThanToken(ComparisonToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class GreaterOrEqualToken(ComparisonToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


class SmallerOrEqualToken(ComparisonToken):
    def __init__(self, line_nr: int):
        super().__init__(line_nr)


special_character_map = {
    "{": ScopeOpenToken,
    "}": ScopeCloseToken,
    "(": ArgumentsOpenToken,
    ")": ArgumentsCloseToken,
    ":": TypehintToken,
    ";": SemiToken,
    "=": AssignmentToken,
}

arithmetic_operator_map = {
    "+": AdditionToken,
    "-": SubtractionToken,
    "*": MultiplicationToken,
}

comparison_operator_map = {
    "==": EqualToken,
    "!=": NotEqualToken,
    ">": GreaterThanToken,
    "<": SmallerThanToken,
    ">=": GreaterOrEqualToken,
    "<=": SmallerOrEqualToken,
}

keywords_list = ["if", "else", "func", "return", "true", "false", "var", "while"]
types_list = ["number", "string", "bool", "void"]
comment_chars = ["#", "//"]


def tokenize_file(filename: str) -> List[LexerToken]:
    with open(filename) as f:
        return reduce(
            list.__add__, map(lambda x: tokenize(x[1], x[0] + 1), enumerate(f.readlines()))
        )


def tokenize_str(txt: str) -> List[LexerToken]:
    return reduce(
        list.__add__, map(lambda x: tokenize(x[1] + "\n", x[0] + 1), enumerate(txt.split("\n")))
    )


def tokenize(txt: str, line_nr=-1, tokens: List[LexerToken] = None) -> List[LexerToken]:
    if tokens == None:
        tokens = []

    token, txt = parse_token(txt, line_nr)
    if token:
        return tokenize(txt, line_nr, tokens + [token])
    return tokens


def parse_token(txt: str, line_nr=-1) -> Tuple[LexerToken, str]:
    txt = skip_whitespaces(txt)

    if len(txt) == 0:
        return None, None

    # Check if this is a comment
    if txt[0] in [c[0] for c in comment_chars]:
        return parse_comment(txt, line_nr)

    # Check if this is a string literal
    if txt[0] == '"':
        return parse_string_literal(txt, line_nr)

    # Check if this character has a special meaning
    if txt[0] in special_character_map and not (len(txt) > 1 and txt[1] == "="):
        return special_character_map[txt[0]](line_nr), txt[1:]

    # Check if this character is a valid operator char
    if txt[0] in [x[0] for x in comparison_operator_map]:
        return parse_operator(txt, line_nr)

    # Check if this is a number literal
    if txt[0].isdigit() or (txt[0] == "-" and txt[1].isdigit()):
        num, txt = eat_number(txt, line_nr)
        return NumberLiteralToken(line_nr, num), txt

    # Check if this is an arithmetic operator
    if txt[0] in arithmetic_operator_map:
        return arithmetic_operator_map[txt[0]](line_nr), txt[1:]

    # Check if this is a argument separator
    if txt[0] == ",":
        return ArgumentSeparatorToken(line_nr), txt[1:]

    token, txt = eat_word(txt)

    if not token:
        raise LexerException(
            "Error on line '{}'. Couldn't lex token around '{}'.".format(line_nr, txt[:16])
        )

    if token in ["true", "false"]:
        return BoolLiteralToken(line_nr, token), txt

    if token in keywords_list:
        return KeywordToken(line_nr, token), txt

    if token in types_list:
        return TypeToken(line_nr, token), txt

    return IdentifierToken(line_nr, token), txt


def parse_comment(txt: str, line_nr=-1, value: str = None) -> Tuple[CommentToken, str]:
    if value == None:
        if txt[0] in ["#", "/"]:
            return parse_comment(txt[1:], line_nr)
        value = ""

    if txt[0] == "\n":
        return CommentToken(line_nr, value), txt
    else:
        return parse_comment(txt[1:], line_nr, value + txt[0])


def parse_string_literal(txt: str, line_nr=-1, value: str = None) -> Tuple[StringLiteralToken, str]:
    if value == None:
        txt = expect_character(txt, '"', line_nr)
        value = ""

    # If string ended
    # TODO: Check for escaped character
    if txt[0] == '"':
        return StringLiteralToken(line_nr, value), txt[1:]
    else:
        return parse_string_literal(txt[1:], line_nr, value + txt[0])


def parse_operator(txt: str, line_nr=-1, operator=None) -> Tuple[ComparisonToken, str]:
    if operator == None:
        txt = skip_whitespaces(txt)
        operator = ""

    valid_char = any([txt[0] in x for x in comparison_operator_map])

    if not valid_char:
        # Parse operator
        if operator in comparison_operator_map:
            return comparison_operator_map[operator](line_nr), txt
        raise LexerException(
            "Error on line {}. Unknown comparison operator '{}'.".format(line_nr, operator)
        )
    else:
        return parse_operator(txt[1:], line_nr, operator + txt[0])


def eat_word(txt: str) -> Tuple[str, str]:
    return eat_while(txt, r"[a-zA-Z_!]")


def eat_number(txt: str, line_nr=-1, eaten: str = None) -> Tuple[str, str]:
    """Eat a number from the text stream.

    Args:
        txt (str): Text stream.
        line_nr (int, optional): Line number. Defaults to -1.
        eaten (str, optional): Already eaten characters, used recursively. Defaults to None.

    Raises:
        LexerException: [description]

    Returns:
        Tuple[str, str]: [description]
    """

    if eaten == None:
        eaten = ""

    first_digit = len(eaten) == 0
    has_decimal_point = "." in eaten

    # Continue eating when the char is a number, or it is a decimal point.
    if len(txt) > 0 and (
        txt[0].isdigit() or (not first_digit and txt[0] == ".") or (first_digit and txt[0] == "-")
    ):
        if txt[0] == ".":
            if has_decimal_point == True:
                raise LexerException(
                    "Error on line {}. Multiple decimal points in number.".format(line_nr)
                )
            has_decimal_point = True

        return eat_number(txt[1:], line_nr, eaten + txt[0])
    else:
        return eaten, txt


def eat_while(txt: str, pattern: str, eaten: str = None) -> Tuple[str, str]:
    """Eat characters from from the text stream as long as the pattern matches.

    Args:
        txt (str): Text stream.
        pattern (str): A regex pattern, all matches are done character-by-character.
        eaten (str, optional): Already eaten characters, used recursively. Defaults to None.

    Returns:
        Tuple[str, str]: Tuple with the eaten characters and the rest of the text stream.
    """

    if eaten == None:
        eaten = ""

    # Return when we find an unwanted character
    if re.match(pattern, txt[0]) == None:
        return eaten, txt
    # Continue eating
    else:
        return eat_while(txt[1:], pattern, eaten + txt[0])


def skip_whitespaces(txt: str) -> str:
    """Skips all whitespaces in the text stream.

    Args:
        txt (str): Text stream.

    Returns:
        str: Text stream, but the front character is not a whitespace character.
    """
    if len(txt) > 0 and txt[0].isspace():
        return skip_whitespaces(txt[1:])
    return txt


def expect_character(txt: str, expected: str, line_nr=-1, _skip_whitespaces=False) -> str:
    """Check if the next character in the stream is the expected character.

    Args:
        txt (str): The text to scan
        expected (str): Expected character (should be exactly one char)
        line_nr (int, optional): Line number at which the char is. Defaults to -1.
        _skip_whitespaces (bool, optional): Defaults to False.

    Raises:
        UnexpectedCharacterException: When the expected character is not found.

    Returns:
        str: The rest of the text stream.
    """

    if _skip_whitespaces:
        txt = skip_whitespaces(txt)

    if txt[0] == expected:
        return txt[1:]
    else:
        raise UnexpectedCharacterException(
            "Error on line {}. Expected '{}', but found '{}'.".format(line_nr, expected, txt[0])
        )


def print_tokens(tokens: List[LexerToken]):
    print(json.dumps(tokens, indent=4, cls=LexerJsonEncoder))


if __name__ == "__main__":

    def print_tokenized_file(filename: str):
        tokens = tokenize_file(filename)
        print("Lexing {}".format(filename))
        print_tokens(tokens)
        print()

    [print_tokenized_file("../example/" + file) for file in os.listdir("../example")]
