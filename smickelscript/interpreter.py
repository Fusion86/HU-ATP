import os
import random
from typing import List, TypeVar, Tuple, Type, Optional, Callable
from functools import reduce
from smickelscript import lexer, parser


SmickelVariableType = TypeVar("SmickelVariableType")


class ProgramState:
    def __init__(self, stack: List = None, retval=None):
        self.stack = stack or [{}]
        self.retval = retval


class SmickelRuntimeException(Exception):
    """Generic runtime exception."""

    pass


class EntrypointNotFoundException(SmickelRuntimeException):
    """Thrown when the entrypoint is not found withing a given program."""

    pass


class UndefinedVariableException(SmickelRuntimeException):
    """Thrown when a variable is used before it has a value."""

    pass


class InvalidImplicitReturnException(SmickelRuntimeException):
    """Thrown when an invalid implicit return statement is evaluated."""

    pass


class InvalidArgumentsException(SmickelRuntimeException):
    """Thrown when the given arguments don't match a functions parameters."""

    pass


class IllegalTypeException(SmickelRuntimeException):
    """Thrown when an illegal type is encounter, for example when intializing a void variable."""

    pass


class IndexOutOfBoundsException(SmickelRuntimeException):
    """Thrown when an array-like object is accessed at an invalid index."""

    pass


class InvalidTypeException(SmickelRuntimeException):
    """Thrown when a given value doesn't match the TypeHint."""

    def __init__(self, line_nr: int, expected_type: Type, actual_type: Type):
        super().__init__(
            "Error on line {}. Expected a value of type '{}' but got a value of type '{}'.".format(
                line_nr, expected_type.__name__, actual_type.__name__
            )
        )


# This is not a good way to do this, but creating a crappy decorator is part of the requirements.
def smickel_trace(func: Callable):
    def wrapper(*args, **kwargs):
        print("TRACE> Executing '{}'".format(func.__name__))
        return func(*args, **kwargs)

    if os.environ.get("SMICKEL_TRACE"):
        return wrapper
    return func


default_stdout = lambda x: print(x, end="")


def run_program(
    ast, entrypoint="main", args=None, stdout: Callable = default_stdout
) -> SmickelVariableType:
    if args == None:
        args = []

    func = find_func(ast, entrypoint)

    if func == None:
        raise EntrypointNotFoundException("Entrypoint '{}' not found.".format(entrypoint))

    return execute_func(ast, func, ProgramState(), stdout, args)[0]


def run_source(source: str, entrypoint="main", args=None, stdout=default_stdout):
    return run_program(parser.load_source(source), entrypoint, args, stdout)


def run_file(filename: str, entrypoint="main", args=None, stdout=default_stdout):
    return run_program(parser.load_file(filename), entrypoint, args, stdout)


def execute(
    ast: List[parser.ParserToken],
    statement: parser.ParserToken,
    state: ProgramState,
    stdout: Callable,
):
    statement_type = type(statement)
    if statement_type in statement_exec_map:
        return statement_exec_map[statement_type](ast, statement, state, stdout)
    else:
        raise NotImplementedError(
            "Statement {} is not implemented.".format(statement_type.__name__)
        )


@smickel_trace
def execute_func_call(
    ast: List[parser.ParserToken],
    statement: parser.FuncCallToken,
    state: ProgramState,
    stdout: Callable,
):
    func_to_call = statement.identifier.value

    if func_to_call in builtin_functions:
        return builtin_functions[func_to_call](ast, statement, state, stdout)

    func = find_func(ast, func_to_call)
    if func:
        # Evaluate the args.
        args, state = execute_args(ast, statement.args, state, stdout)

        # Execute function
        retval, state = execute_func(ast, func, state, stdout, args)

        return retval, state
    else:
        raise SmickelRuntimeException(
            "Can't call function {}, because it could not be found.".format(func_to_call)
        )


@smickel_trace
def execute_noop(ast: List[parser.ParserToken], token, state: ProgramState, stdout: Callable):
    return None, state


@smickel_trace
def execute_func(
    ast: List[parser.ParserToken],
    func: parser.FunctionToken,
    state: ProgramState,
    stdout: Callable,
    args: List,
):
    # Check that we have enough args.
    if len(args) != len(func.parameters):
        raise InvalidArgumentsException(
            "Error on line {}. Function '{}' expects {} parameters, but it got {} parameters.".format(
                func.identifier.line_nr, func.identifier.value, len(func.parameters), len(args)
            )
        )

    # Extract param names.
    para_names = map(lambda x: x.identifier.value, func.parameters)

    # Verify types.
    list(map(lambda x: verify_type(x[0].variable_type, x[1]), zip(func.parameters, args)))

    # Create new stack scope and push the arguments.
    new_stack_layer = dict(zip(para_names, args))
    state = ProgramState(state.stack + [new_stack_layer])

    # Execute body and verify return type.
    retval, state = execute_scope(ast, func.body, state, stdout, False)
    verify_type(func.return_type, retval)

    # Pop stack.
    state = ProgramState(state.stack[:-1])

    return retval, state


@smickel_trace
def execute_scope(
    ast: List[parser.ParserToken],
    scope: parser.ScopeWithBody,
    state: ProgramState,
    stdout: Callable,
    create_new_stack_layer=True,
    counter=0,
):
    # Init new stack layer on first run (if wanted).
    if create_new_stack_layer and counter == 0:
        state = ProgramState(state.stack + [{}])

    # If we reached the end of the scope.
    if len(scope.body) <= counter:
        # Pop stack only if we also were the ones to create it.
        if create_new_stack_layer:
            state = ProgramState(state.stack[:-1])
        return None, state

    # Else just continue executing the scope.
    retval, state = execute(ast, scope.body[counter], state, stdout)

    # Return when a return value is given.
    # TODO: This also returns when a user does something like `"Hello"`, even without the return keyword!
    if retval != None:
        # Throw an error if the implicit return is not the last statement in the body and not a statements_that_may_return.
        if (
            len(scope.body) != counter + 1
            and type(scope.body[counter]) not in explicit_return_statements
        ):
            if isinstance(scope.body[counter], lexer.ValueToken):
                line_nr = scope.body[counter].line_nr
            else:
                line_nr = scope.body[counter].value.line_nr
            raise InvalidImplicitReturnException(
                "Error on line {}. This implicit return statement is not the last statement in its scope.".format(
                    line_nr
                )
            )

        # Pop stack only if we also were the ones to create it.
        if create_new_stack_layer:
            state = ProgramState(state.stack[:-1])
        return retval, state

    return execute_scope(ast, scope, state, stdout, create_new_stack_layer, counter + 1)


@smickel_trace
def execute_init_var(
    ast: List[parser.ParserToken],
    token: parser.InitVariableToken,
    state: ProgramState,
    stdout: Callable,
):
    if token.variable_type.type_name == "void":
        raise IllegalTypeException(
            "Error on line {}. A variable can't have the type 'void'.".format(
                token.identifier.line_nr
            )
        )

    value, state = execute(ast, token.value, state, stdout)
    verify_type(token.variable_type, value)

    # The code below does the same as this line:
    # state.stack[-1][token.identifier.value] = value

    state = ProgramState(
        state.stack[:-1]
        + [dict(list(state.stack[-1].items()) + list({token.identifier.value: value}.items()))]
    )
    return None, state


@smickel_trace
def execute_identifier(
    ast: List[parser.ParserToken],
    token: lexer.IdentifierToken,
    state: ProgramState,
    stdout: Callable,
):
    return get_var_value(token, state), state


@smickel_trace
def execute_literal(
    ast: List[parser.ParserToken], token: parser.LiteralToken, state: ProgramState, stdout: Callable
) -> Tuple[SmickelVariableType, ProgramState]:
    if type(token.value) == lexer.NumberLiteralToken:
        return int(token.value.value), state
    return token.value.value, state


@smickel_trace
def execute_args(
    ast: List[parser.ParserToken], args: List, state: ProgramState, stdout: Callable, retval=None
):
    if retval == None:
        retval = []

    if len(args) > 0:
        val, state = execute(ast, args[0], state, stdout)
        return execute_args(ast, args[1:], state, stdout, retval + [val])
    else:
        return retval, state


@smickel_trace
def execute_var_assignment(
    ast: List[parser.ParserToken],
    token: parser.AssignVariableToken,
    state: ProgramState,
    stdout: Callable,
):
    value, state = execute(ast, token.value, state, stdout)
    assign_var_value(state, token.identifier.value, value)

    # A variable assignment does NOT return a value.
    return None, state


@smickel_trace
def execute_operator(
    ast: List[parser.ParserToken],
    token: parser.OperatorToken,
    state: ProgramState,
    stdout: Callable,
):
    lhs, state = execute(ast, token.lhs, state, stdout)
    rhs, state = execute(ast, token.rhs, state, stdout)
    op_type = type(token.operator)
    if op_type in operators_map:
        return operators_map[op_type](lhs, rhs), state
    else:
        raise NotImplementedError("Operator '{}' is not implemented.".format(op_type))


@smickel_trace
def execute_if(
    ast: List[parser.ParserToken],
    token: parser.IfStatementToken,
    state: ProgramState,
    stdout: Callable,
):
    value, state = execute(ast, token.condition, state, stdout)
    if value:
        return execute(ast, token.true_body, state, stdout)
    else:
        return None, state


@smickel_trace
def execute_return(
    ast: List[parser.ParserToken], token: parser.ReturnToken, state: ProgramState, stdout: Callable
):
    return execute(ast, token.value, state, stdout)


@smickel_trace
def execute_while(
    ast: List[parser.ParserToken],
    token: parser.WhileStatementToken,
    state: ProgramState,
    stdout: Callable,
):
    value, state = execute(ast, token.condition, state, stdout)
    if value:
        retval, state = execute(ast, token.body, state, stdout)

        if retval != None:
            return retval, state

        return execute_while(ast, token, state, stdout)
    return None, state


@smickel_trace
def execute_index_access(
    ast: List[parser.ParserToken],
    token: parser.IndexAccessToken,
    state: ProgramState,
    stdout: Callable,
):
    value, state = execute(ast, token.identifier, state, stdout)
    idx, state = execute(ast, token.index, state, stdout)

    try:
        return value[idx], state
    except IndexError:
        raise IndexOutOfBoundsException(
            "Error on line {}. Can't access object at index {}.".format(
                token.identifier.line_nr, idx
            )
        )


@smickel_trace
def execute_init_fixed_size_array(
    ast: List[parser.ParserToken],
    token: parser.FixedSizeArrayToken,
    state: ProgramState,
    stdout: Callable,
):
    size, state = execute(ast, token.size, state, stdout)
    if token.init_value:
        val, state = execute(ast, token.init_value, state, stdout)
        if type(val) == str:
            chars = list(val)

            if len(chars) > size:
                raise SmickelRuntimeException(
                    "Error on line {}. String literal is larger than the array size.".format(
                        token.init_value.value.line_nr
                    )
                )
            arr = chars + [0] * (size - len(chars))
            return arr, state
        else:
            raise NotImplementedError()
    else:
        return [0] * size, state


@smickel_trace
def execute_array_insert(
    ast: List[parser.ParserToken],
    token: parser.ArrayInsertToken,
    state: ProgramState,
    stdout: Callable,
):
    arr = get_var_value(token.array.identifier, state)[:]
    idx, state = execute(ast, token.array.index, state, stdout)
    value, state = execute(ast, token.value, state, stdout)
    arr[idx] = value
    state = assign_var_value(state, token.array.identifier.value, arr)
    return None, state


@smickel_trace
def execute_print(
    ast: List[parser.ParserToken],
    statement: parser.FuncCallToken,
    state: ProgramState,
    stdout: Callable,
    end="\n",
):
    args, state = execute_args(ast, statement.args, state, stdout)
    if len(args) > 1:
        raise SmickelRuntimeException("print doesn't accept more than one argument.")
    stdout((str(args[0]) if len(args) == 1 else "") + end)
    return None, state


@smickel_trace
def execute_rand(
    ast: List[parser.ParserToken],
    statement: parser.FuncCallToken,
    state: ProgramState,
    stdout: Callable,
):
    args, state = execute_args(ast, statement.args, state, stdout)
    if len(args) == 0:
        a, b = (0, 1)
    elif len(args) == 1:
        a, b = (0, args[0])
    else:
        a, b = args
    return random.randint(a, b), state


def find_func(ast: List[parser.ParserToken], func_name: str) -> Optional[parser.FunctionToken]:
    # return next(
    #     (x for x in ast if type(x) == parser.FunctionToken and x.identifier.value == func_name),
    #     None,
    # )

    funcs = [x for x in ast if type(x) == parser.FunctionToken and x.identifier.value == func_name]
    if len(funcs) == 0:
        return None
    elif len(funcs) > 1:
        raise SmickelRuntimeException(
            "There are more than one '{}' functions. This is not supported.".format(func_name)
        )
    return funcs[0]


def get_var_value(token: lexer.IdentifierToken, state: ProgramState) -> SmickelVariableType:
    def get_value(layer):
        if token.value in layer:
            return layer[token.value]

    values = [x for x in map(get_value, state.stack) if x != None]

    if len(values) == 0:
        raise UndefinedVariableException(
            "Error on line {}. Undefined variable '{}'.".format(token.line_nr, token.value)
        )

    # Return the value in the highest/closest stack
    return values[-1]


def assign_var_value(state: ProgramState, var_name: str, value, layer: int = None) -> ProgramState:
    """Assing 'var_name' to 'value' in the first stack layer where it is found.

    Args:
        state (ProgramState):
        var_name (str): The name of the value to assign.
        value ([type]): The value which the var should be set to.
        layer (int, optional): The layer in which to start looking. Defaults to None which means the top layer.

    Raises:
        SmickelRuntimeException: When a variable is not found. Should NEVER happen, but it's here to ensure that we know about it in the impossible case that it does.

    Returns:
        ProgramState: The new program state, in which the variable is assigned to the value.
    """

    if layer == None:
        layer = len(state.stack) - 1

    if var_name in state.stack[layer]:
        state.stack[layer][var_name] = value
        return state
    elif layer > 1:
        return assign_var_value(state, var_name, value, layer - 1)
    else:
        raise SmickelRuntimeException("Couldn't find variable to assign. This should never happen.")


def verify_type(type_token: lexer.TypeToken, value):
    if type_token.type_name == "number":
        if type(value) != int:
            raise InvalidTypeException(type_token.line_nr, int, type(value))
    elif type_token.type_name == "string":
        if type(value) != str:
            raise InvalidTypeException(type_token.line_nr, int, type(value))
    else:
        # No type given, or the type is not implemented.
        pass


builtin_functions = {
    "println": execute_print,
    "print": lambda *x: execute_print(*x, end=""),
    "rand": execute_rand,
}

statement_exec_map = {
    parser.FuncCallToken: execute_func_call,
    parser.LiteralToken: execute_literal,
    parser.ScopeWithBody: execute_scope,
    parser.InitVariableToken: execute_init_var,
    lexer.IdentifierToken: execute_identifier,
    lexer.CommentToken: execute_noop,
    parser.AssignVariableToken: execute_var_assignment,
    parser.OperatorToken: execute_operator,
    parser.IfStatementToken: execute_if,
    parser.ReturnToken: execute_return,
    parser.WhileStatementToken: execute_while,
    parser.IndexAccessToken: execute_index_access,
    parser.FixedSizeArrayToken: execute_init_fixed_size_array,
    parser.ArrayInsertToken: execute_array_insert,
}

operators_map = {
    # Arithmetic
    lexer.AdditionToken: lambda a, b: a + b,
    lexer.SubtractionToken: lambda a, b: a - b,
    lexer.MultiplicationToken: lambda a, b: a * b,
    # Comparison
    lexer.EqualToken: lambda a, b: a == b,
    lexer.NotEqualToken: lambda a, b: a != b,
    lexer.GreaterThanToken: lambda a, b: a > b,
    lexer.SmallerThanToken: lambda a, b: a < b,
    lexer.GreaterOrEqualToken: lambda a, b: a >= b,
    lexer.SmallerOrEqualToken: lambda a, b: a <= b,
}

explicit_return_statements = [
    parser.ReturnToken,
    parser.IfStatementToken,
    parser.WhileStatementToken,
]
