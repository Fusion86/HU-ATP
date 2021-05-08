import os
from typing import List, TypeVar, Tuple, Type
from functools import reduce
from smickelscript import lexer, parser


T = TypeVar("T")
SmickelVariableType = TypeVar("SmickelVariableType")


class ProgramState:
    def __init__(self, stack: List = None, retval=None):
        self.stack = stack or [{}]
        self.retval = retval


class SmickelRuntimeException(Exception):
    pass


class EntrypointNotFoundException(SmickelRuntimeException):
    pass


class UndefinedVariableException(SmickelRuntimeException):
    pass


class InvalidTypeException(SmickelRuntimeException):
    def __init__(self, line_nr: int, expected_type: Type, actual_type: Type):
        super().__init__(
            "Error on line {}. Expected a value of type '{}' but got a value of type '{}'.".format(
                line_nr, expected_type.__name__, actual_type.__name__
            )
        )


default_stdout = lambda x: print(x, end="")


def run_program(ast, entrypoint="main", stdout=default_stdout) -> SmickelVariableType:
    func = find_func(ast, entrypoint)

    if func == None:
        raise EntrypointNotFoundException("Entrypoint '{}' not found.".format(entrypoint))

    return execute_func(ast, func, ProgramState(), stdout)[0]


def run_source(source: str, entrypoint="main", stdout=default_stdout):
    return run_program(parser.load_source(source), entrypoint, stdout)


def run_file(filename: str, entrypoint="main", stdout=default_stdout):
    return run_program(parser.load_file(filename), entrypoint, stdout)


def execute(ast, statement, state: ProgramState, stdout):
    statement_type = type(statement)
    if statement_type in statement_exec_map:
        return statement_exec_map[statement_type](ast, statement, state, stdout)
    else:
        raise NotImplementedError(statement_type)


def execute_func_call(ast, statement: parser.FuncCallToken, state: ProgramState, stdout):
    func_to_call = statement.identifier.value

    if func_to_call == "println":
        args, state = execute_args(ast, statement.args, state, stdout)
        if len(args) > 1:
            raise SmickelRuntimeException("println doesn't accept more than one argument.")
        stdout((str(args[0]) if len(args) == 1 else "") + "\n")
        return None, state

    func = find_func(ast, func_to_call)
    if func:
        # Evaluate the args.
        args, state = execute_args(ast, statement.args, state, stdout)

        # Extract param names
        para_names = map(lambda x: x.identifier.value, func.parameters)

        # Verify types
        list(map(lambda x: verify_type(x[0].variable_type, x[1]), zip(func.parameters, args)))

        # Create new stack scope and push the arguments
        new_stack_layer = dict(zip(para_names, args))
        state = ProgramState(state.stack + [new_stack_layer])

        # Execute function
        retval, state = execute_func(ast, func, state, stdout)

        # Pop stack
        state = ProgramState(state.stack[:-1])
        return retval, state
    else:
        raise Exception(
            "Can't call function '{}', because it could not be found.".format(func_to_call)
        )


def execute_noop(ast: List, token, state: ProgramState, stdout):
    return None, state


def execute_func(ast: List, func: parser.FunctionToken, state: ProgramState, stdout):
    retval, state = execute_scope(ast, func.body, state, stdout, False)
    verify_type(func.return_type, retval)
    return retval, state


def execute_scope(
    ast: List,
    scope: parser.ScopeWithBody,
    state: ProgramState,
    stdout,
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

    # If this is a return statement.
    # if type(scope.body[counter]) == parser.ReturnToken:
    #     retval, state = execute(ast, scope.body[counter].value, state, stdout)

    #     # Pop stack only if we also were the ones to create it.
    #     if create_new_stack_layer:
    #         state = ProgramState(state.stack[:-1])

    #     return retval, state

    # Else just continue executing the scope.
    retval, state = execute(ast, scope.body[counter], state, stdout)

    if retval != None:
        # Pop stack only if we also were the ones to create it.
        if create_new_stack_layer:
            state = ProgramState(state.stack[:-1])
        return retval, state

    return execute_scope(ast, scope, state, stdout, create_new_stack_layer, counter + 1)


def execute_init_var(ast: List, token: parser.InitVariableToken, state: ProgramState, stdout):
    value, state = execute(ast, token.value, state, stdout)

    # The code below does the same as this line:
    # state.stack[-1][token.identifier.value] = value

    state = ProgramState(
        state.stack[:-1]
        + [dict(list(state.stack[-1].items()) + list({token.identifier.value: value}.items()))]
    )
    return None, state


def execute_identifier(ast: List, token: lexer.IdentifierToken, state: ProgramState, stdout):
    return get_var_value(token, state), state


def execute_literal(
    ast: List, token: parser.LiteralToken, state: ProgramState, stdout
) -> Tuple[SmickelVariableType, ProgramState]:
    if type(token.value) == lexer.NumberLiteralToken:
        return int(token.value.value), state
    return token.value.value, state


def execute_args(ast: List, args: List, state: ProgramState, stdout, retval=None):
    if retval == None:
        retval = []

    if len(args) > 0:
        val, state = execute(ast, args[0], state, stdout)
        return execute_args(ast, args[1:], state, stdout, [val] + retval)
    else:
        return retval, state


def execute_var_assignment(
    ast: List, token: parser.AssignVariableToken, state: ProgramState, stdout
):
    # def find_layer_with_value(layer):
    #     if token.identifier.value in layer:
    #         return layer

    value, state = execute(ast, token.value, state, stdout)

    # stacks_with_value = [x for x in map(find_layer_with_value, state.stack) if x != None]

    # var_set = False
    # newstack = list(
    #     map(
    #         lambda x: (
    #             [dict(list(x.items()) + list({token.identifier.value: value}.items()))]
    #             if token.identifier.value in x
    #             else x
    #         ),
    #         state.stack,
    #     )
    # )

    # def krins(a, b):
    #     if type(a) == lexer.IdentifierToken:
    #         b[token.identifier.value] = value
    #         return b

    #     return b

    # newstack = reduce(krins, [token.identifier, *state.stack])

    # TODO: Make this functional
    for layer in reversed(state.stack):
        if token.identifier.value in layer:
            layer[token.identifier.value] = value
            break

    # A variable assignment does NOT return a value.
    return None, state


def execute_operator(ast: List, token: parser.OperatorToken, state: ProgramState, stdout):
    lhs, state = execute(ast, token.lhs, state, stdout)
    rhs, state = execute(ast, token.rhs, state, stdout)
    op_type = type(token.operator)
    if op_type in operators_map:
        return operators_map[op_type](lhs, rhs), state
    else:
        raise NotImplementedError("Operator '{}' is not implemented.".format(op_type))


def execute_if(ast: List, token: parser.IfStatementToken, state: ProgramState, stdout):
    value, state = execute(ast, token.condition, state, stdout)
    if value:
        return execute(ast, token.true_body, state, stdout)
    else:
        return None, state


def execute_return(ast: List, token: parser.ReturnToken, state: ProgramState, stdout):
    return execute(ast, token.value, state, stdout)


def execute_while(ast: List, token: parser.WhileStatementToken, state: ProgramState, stdout):
    value, state = execute(ast, token.condition, state, stdout)
    if value:
        retval, state = execute(ast, token.body, state, stdout)
        return execute_while(ast, token, state, stdout)
    return None, state


def find_func(ast, func_name) -> parser.FunctionToken:
    return next(
        (x for x in ast if type(x) == parser.FunctionToken and x.identifier.value == func_name),
        None,
    )


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


def verify_type(type_token: lexer.TypeToken, value):
    if type_token.type_name == "number":
        if type(value) != int:
            raise InvalidTypeException(type_token.line_nr, int, type(value))
    elif type_token.type_name == "string":
        if type(value) != str:
            raise InvalidTypeException(type_token.line_nr, int, type(value))


statement_exec_map = {
    parser.FuncCallToken: execute_func_call,
    # parser.FunctionToken: execute_func,
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
}

operators_map = {
    # Arithmetic
    lexer.AdditionToken: lambda a, b: a + b,
    lexer.SubtractionToken: lambda a, b: a - b,
    # Comparison
    lexer.EqualToken: lambda a, b: a == b,
    lexer.GreaterOrEqualToken: lambda a, b: a >= b,
}

if __name__ == "__main__":
    run_file("../example/hello_world.suc")
    run_file("../example/hello_world_indirect.suc")
    # run_file("../example/multi_scope.suc")
