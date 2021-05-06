import os
import re
import json
import types
import jsonpickle
import itertools
from enum import Enum, unique
from functools import reduce
from typing import List, Tuple, Union, Iterable
from pprint import pprint


class LexerException(Exception):
    pass


class UnexpectedCharacterException(Exception):
    pass


class LexerJsonEncoder(json.JSONEncoder):
    def default(self, o):
        return {"__type": type(o).__name__, **o.__dict__}


class LexerToken:
    def __init__(self, line_nr):
        self.line_nr = line_nr

    def __repr__(self):
        return "<{}>".format(type(self).__name__)


class KeywordToken(LexerToken):
    def __init__(self, line_nr, value):
        super().__init__(line_nr)
        self.value = value

    def __repr__(self):
        return "<KeywordToken value: {}>".format(self.value)


class TypeToken(LexerToken):
    def __init__(self, line_nr, type_name):
        super().__init__(line_nr)
        self.type_name = type_name


class IdentifierToken(LexerToken):
    def __init__(self, line_nr, value):
        super().__init__(line_nr)
        self.value = value


class StringLiteralToken(LexerToken):
    def __init__(self, line_nr, value):
        super().__init__(line_nr)
        self.value = value


class NumberLiteralToken(LexerToken):
    def __init__(self, line_nr, value):
        super().__init__(line_nr)
        self.value = value


class CommentToken(LexerToken):
    def __init__(self, line_nr, value):
        super().__init__(line_nr)
        self.value = value


class ScopeOpenToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class ScopeCloseToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class ArgumentsOpenToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class ArgumentsCloseToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class TypehintToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class SemiToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class ArithmeticToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class AdditionToken(ArithmeticToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class SubtractionToken(ArithmeticToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class MultiplicationToken(ArithmeticToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class AssignmentToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class ComparisonToken(LexerToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class EqualToken(ComparisonToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class NotEqualToken(ComparisonToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class GreaterThanToken(ComparisonToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class SmallerThanToken(ComparisonToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class GreaterOrEqualToken(ComparisonToken):
    def __init__(self, line_nr):
        super().__init__(line_nr)


class SmallerOrEqualToken(ComparisonToken):
    def __init__(self, line_nr):
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


def tokenize_file(filename: str):
    with open(filename) as f:
        return reduce(
            list.__add__, map(lambda x: tokenize(x[1], x[0] + 1), enumerate(f.readlines()))
        )


def tokenize(txt: str, line_nr=-1, tokens: List[LexerToken] = None):
    if tokens == None:
        tokens = []

    token, txt = parse_token(txt, line_nr)
    if token:
        return tokenize(txt, line_nr, tokens + [token])
    return tokens


def parse_token(txt: str, line_nr=-1):
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

    # Check if this is an arithmetic operator
    if txt[0] in arithmetic_operator_map:
        return arithmetic_operator_map[txt[0]](line_nr), txt[1:]

    # Check if this is a number literal
    if txt[0].isdigit() or (txt[0] == "-" and txt[1].isdigit()):
        num, txt = eat_number(txt, line_nr)
        return NumberLiteralToken(line_nr, num), txt

    token, txt = eat_word(txt)

    if not token:
        raise LexerException(
            "Error on line '{}'. Couldn't lex token around '{}'.".format(line_nr, txt[:16])
        )

    if token in keywords_list:
        return KeywordToken(line_nr, token), txt

    if token in types_list:
        return TypeToken(line_nr, token), txt

    return IdentifierToken(line_nr, token), txt


def parse_comment(txt: str, line_nr=-1, value: str = None):
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


def parse_operator(txt: str, line_nr=-1, operator=None):
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


def eat_word(txt: str):
    return eat_while(txt, r"[a-zA-Z_!]")


def eat_number(txt: str, line_nr=-1, eaten: str = None, first_digit=True, has_decimal_point=False):
    if eaten == None:
        eaten = ""

    # Continue eating when the char is a number, or it is a decimal point.
    if txt[0].isdigit() or (not first_digit and txt[0] == ".") or (first_digit and txt[0] == "-"):
        if txt[0] == ".":
            if has_decimal_point == True:
                raise LexerException(
                    "Error on line {}. Multiple decimal points in number.".format(line_nr)
                )
            has_decimal_point = True

        return eat_number(txt[1:], line_nr, eaten + txt[0], False, has_decimal_point)
    # Continue eating
    else:
        return eaten, txt


def eat_while(txt: str, pattern: str, eaten: str = None):
    if eaten == None:
        eaten = ""

    # Return when we find an unwanted character
    if re.match(pattern, txt[0]) == None:
        return eaten, txt
    # Continue eating
    else:
        return eat_while(txt[1:], pattern, eaten + txt[0])


def skip_whitespaces(txt: str) -> str:
    if len(txt) > 0 and txt[0].isspace():
        return skip_whitespaces(txt[1:])
    return txt


def expect_character(txt: str, expected: str, line_nr=-1, _skip_whitespaces=False):
    """
    Check if the next character in the stream is the expected character.
    If it is the stream pos will be incremented with one, if not the stream will be left untouched.
    If skip_whitespaces is True the stream will be incremented for each skipped whitespace.
    """

    if _skip_whitespaces:
        txt = skip_whitespaces(txt)

    if txt[0] == expected:
        return txt[1:]
    else:
        raise UnexpectedCharacterException(
            "Error on line {}. Expected '{}', but found '{}'.".format(line_nr, expected, txt[0])
        )


if __name__ == "__main__":

    def print_tokenized_file(filename: str):
        tokens = tokenize_file(filename)
        print("Lexing {}".format(filename))
        print(json.dumps(tokens, indent=2, cls=LexerJsonEncoder))
        print()

    [print_tokenized_file("../code/" + file) for file in os.listdir("../code")]
