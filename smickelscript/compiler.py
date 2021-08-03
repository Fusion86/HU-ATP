import secrets
from typing import List, TypeVar, Tuple, Type, Optional, Callable
from smickelscript import lexer, parser


class SmickelCompilerException(Exception):
    """Generic compiler exception."""

    pass


class IllegalFunctionCallException(SmickelCompilerException):
    """Thrown when a function call is not valid."""

    pass


class UndefinedVariableException(SmickelCompilerException):
    """Thrown when a variable is used before it has a value."""

    pass


class IllegalTypeException(SmickelCompilerException):
    """Thrown when an illegal type is encounter, for example when intializing a void variable."""

    pass


class AsmData:
    def __init__(self, data=None, stack=None):
        self.data = data or {}
        self.stack = stack or []


def compile_source(source: str) -> str:
    return compile(parser.load_source(source))


def compile(ast: List[parser.ParserToken], data: AsmData = None):
    def declare_variable(name, value):
        # TODO: Currently this only works for string literals
        return f'{name}:\n  .{value[0]} "{value[1]}"'

    if data == None:
        data = AsmData()

    src, data = compile_token(ast[0], data)

    if len(ast) > 1:
        return compile(ast[1:], data) + src

    full_src = ".cpu cortex-m0\n.align 2\n\n.data\n\n"
    full_src += "\n".join([declare_variable(x, data.data[x]) for x in data.data])
    full_src += "\n\n.text\n.global smickelscript_entry\n"
    full_src += src
    return full_src


def compile_token(statement: parser.ParserToken, data: AsmData):
    statement_type = type(statement)
    if statement_type in token_compilers:
        return token_compilers[statement_type](statement, data)
    else:
        raise NotImplementedError(
            "Statement {} is not implemented.".format(statement_type.__name__)
        )


def compile_func(statement: parser.FunctionToken, data: AsmData):
    data = AsmData(data.data.copy(), data.stack[:])

    # Rename main to smickel_main
    func_name = statement.identifier.value
    if func_name == "main":
        func_name = "smickelscript_entry"

    if len(statement.parameters) > 1:
        raise SmickelCompilerException(
            "Error on line {}. Function {} can't have more than 1 parameters.".format(
                statement.identifier.line_nr, statement.identifier.value
            )
        )

    # Link parameter names to their registers
    # Function parameters will be saved in r4 register
    # This could be changed to allow for more registers, but that'd also require changes
    # in other places. I can't really be bothered to support it, so for now you are only
    # allowed to pass one parameter to a function.
    names = [x.identifier.value for x in statement.parameters]
    registers = [f"r{x+4}" for x in range(0, len(statement.parameters))]
    stack_layer = dict(zip(names, registers))
    data.stack.append(stack_layer)

    body_src, data = compile_scope(statement.body, data, True)
    src = f"\n@ Function {statement.identifier.value} on line {statement.identifier.line_nr}\n"
    src += f"{func_name}:\n"
    src += body_src
    return src, data


def compile_func_call(token: parser.FuncCallToken, data: AsmData):
    data = AsmData(data.data.copy(), data.stack[:])

    def compile_push_var(nr, var):
        if type(var) == parser.OperatorToken or type(var) == parser.FuncCallToken:
            return compile_token(var, data)[0]
        elif type(var.value) == lexer.StringLiteralToken:
            var_name = f"lit_{len(data.data)}"
            data.data[var_name] = ["asciz", var.value.value]
            dbg = f"  @ Loading variable ({nr}, {type(var.value).__name__}) on line {var.value.line_nr}\n"
            return dbg + f"  ldr r{nr}, ={var_name}\n"
        elif type(var.value) == lexer.NumberLiteralToken:
            dbg = f"  @ Loading variable ({nr}, {type(var.value).__name__}) on line {var.value.line_nr}\n"
            return dbg + f"  mov r{nr}, #{var.value.value}\n"
        else:
            raise NotImplementedError()

    if len(token.args) > 1:
        raise IllegalFunctionCallException("Can't have more than 1 function arguments.")

    src = f"  @ Function call to {token.identifier.value} on line {token.identifier.line_nr}\n"
    src += "\n".join([compile_push_var(k, v) for k, v in enumerate(token.args)])
    src += f"  bl {token.identifier.value}\n"
    return src, data


def compile_literal(token: parser.LiteralToken, data: AsmData, register="r0"):
    value_type = type(token.value)
    if value_type == lexer.BoolLiteralToken:
        return f"  mov {register}, #{1 if token.value.value == 'true' else 0}\n", data
    elif value_type == lexer.NumberLiteralToken:
        return f"  mov {register}, #{token.value.value}\n", data
    raise NotImplementedError(
        "Error on line {}. Literal of type {} is not implemented.".format(
            token.value.line_nr, value_type.__name__
        )
    )


def compile_scope(scope: parser.ScopeWithBody, data: AsmData, create_stack_layer=False, counter=0):
    src = ""
    if create_stack_layer and counter == 0:
        # Push registers we are not allowed to change to the stack.
        # Also moves the r0 register (function parameter) to the r4 register,
        # we do this because some instructions change the r0 register which
        # would cause us to lose our parameter value.
        src += "  push { r4, r5, r6, lr }\n  mov r4, r0\n"

    if len(scope.body) <= counter:
        if create_stack_layer:
            return "  pop { r4, r5, r6, pc }\n", data
        else:
            return "", data

    src_token, data = compile_token(scope.body[counter], data)
    src_rest, data = compile_scope(scope, data, create_stack_layer, counter + 1)
    return src + src_token + src_rest, data


def compile_if_statement(token: parser.IfStatementToken, data: AsmData):
    src_condition, data = compile_operator(token.condition, data)

    if_statement_id = secrets.token_hex(5)
    true_label = "if_" + if_statement_id + "_true"
    end_label = "if_" + if_statement_id + "_end"

    x, data = compile_scope(token.true_body, data)
    src_true = true_label + ":\n@ True body\n" + x
    src_false = "  @ False body\n"

    if token.false_body != None:
        x, data = compile_scope(token.false_body, data)
        src_false += x
    src_false += f"  b {end_label}\n"

    condition_type = type(token.condition.operator)
    if condition_type in condition_type_map:
        op = condition_type_map[condition_type]
        src_jump_true = f"  {op} {true_label}\n"

        src = (
            "  @ Conditional statement\n"
            + src_condition
            + src_jump_true
            + src_false
            + src_true
            + f"{end_label}:\n"
        )

        return src, data
    else:
        raise NotImplementedError("Condition not implemented.")


def compile_operator(token: parser.OperatorToken, data: AsmData, dst_register="r0"):
    src_load_lhs, data = compile_load_var("r0", token.lhs, data)
    src_load_rhs, data = compile_load_var("r1", token.rhs, data)
    if isinstance(token.operator, lexer.ComparisonToken):
        src_condition = "  cmp r0, r1\n"
    elif isinstance(token.operator, lexer.SubtractionToken):
        src_condition = f"  sub {dst_register}, r0, r1\n"
    elif isinstance(token.operator, lexer.AdditionToken):
        src_condition = f"  add {dst_register}, r0, r1\n"
    else:
        raise NotImplementedError(
            "Error on line {}. Operator '{}' is not implemented.".format(
                token.operator.line_nr, token.operator
            )
        )
    dbg = f"  @ {token.operator} on line {token.operator.line_nr}\n"
    return dbg + src_load_lhs + src_load_rhs + src_condition, data


def compile_return_statement(token: parser.ReturnToken, data: AsmData):
    src, data = compile_token(token.value, data)
    return src + "  pop { r4, r5, r6, pc }\n", data


def compile_init_var(token: parser.InitVariableToken, data: AsmData):
    if token.variable_type.type_name == "void":
        raise IllegalTypeException(
            "Error on line {}. A variable can't have the type 'void'.".format(
                token.identifier.line_nr
            )
        )

    # Figure out where to save the variable
    data = AsmData(data.data.copy(), data.stack[:])
    reg = f"r{4 + len(data.stack[-1])}"
    data.stack[-1][token.identifier.value] = reg

    src, data = compile_literal(token.value, data, reg)
    # `token.value.value.value` tragic code :(
    dbg = f"  @ Init variable '{token.identifier.value}' with value '{token.value.value.value}' on line {token.identifier.line_nr}\n"

    return dbg + src, data


def compile_while(token: parser.WhileStatementToken, data: AsmData):
    while_label = "while_" + secrets.token_hex(5)

    body_src, data = compile_scope(token.body, data)
    condition_src, data = compile_operator(token.condition, data)

    condition_type = type(token.condition.operator)
    if condition_type in condition_type_map:
        op = condition_type_map[condition_type]
        src_jump_true = f"  {op} {while_label}\n"

        line_nr = token.condition.operator.line_nr
        src = f"  @ While statement on line {line_nr}\n"
        src += while_label + ":\n"
        src += body_src
        src += condition_src
        src += src_jump_true

        return src, data
    else:
        raise NotImplementedError()


def compile_assign_var(token: parser.AssignVariableToken, data: AsmData):
    data = AsmData(data.data.copy(), data.stack[:])

    # Figure out where to store the result
    if token.identifier.value in data.stack[-1]:
        reg = data.stack[-1][token.identifier.value]
    else:
        raise SmickelCompilerException(
            "Variable '{}' not found in the current stack layer. Assigning variables in a higher stack layer is currently not supported.".format(
                token.identifier.value
            )
        )

    # Evaluate the value
    if isinstance(token.value, parser.OperatorToken):
        # Optimization to directly store the resulting value in the correct register.
        src, data = compile_operator(token.value, data, reg)
    else:
        # This is less optimized as we need to move the resulting value to the correct register.
        # It only takes 1 more instruction, but is technically less performant.

        # Evaluate value
        src, data = compile_token(token.value, data)

        # Store the result in the correct register
        src += f"  mov {reg}, r0"

    return src, data


def compile_identifier(token: lexer.IdentifierToken, data: AsmData):
    src, value = get_var_value(token, data)
    dbg = f"  @ Return statement on line {token.line_nr}\n"
    return dbg + src + f"  mov r0, {value}\n", data


def compile_load_var(register, var, data: AsmData):
    src, value = get_var_value(var, data)
    return src + f"  mov {register}, {value}\n", data


def get_var_value(token: lexer.ValueToken, data: AsmData):
    def get_value(layer):
        if token.value in layer:
            # TODO: Also add in which layer this value is
            return "", layer[token.value]

    if type(token) == parser.LiteralToken:
        if type(token.value) == lexer.NumberLiteralToken:
            return "", f"#{token.value.value}"
        elif type(token.value) == lexer.BoolLiteralToken:
            return "", f"#{1 if token.value.value == 'true' else 0}"
        else:
            raise NotImplementedError()

    values = [x for x in map(get_value, data.stack) if x != None]

    if len(values) == 0:
        raise UndefinedVariableException(
            "Error on line {}. Undefined variable '{}'.".format(token.line_nr, token.value)
        )

    # Return the value in the highest/closest stack
    return values[-1]


token_compilers = {
    parser.FunctionToken: compile_func,
    parser.LiteralToken: compile_literal,
    parser.OperatorToken: compile_operator,
    parser.FuncCallToken: compile_func_call,
    parser.IfStatementToken: compile_if_statement,
    parser.ReturnToken: compile_return_statement,
    parser.InitVariableToken: compile_init_var,
    parser.WhileStatementToken: compile_while,
    parser.AssignVariableToken: compile_assign_var,
    lexer.IdentifierToken: compile_identifier,
}

# This map should return the operator which does the inverse.
condition_type_map = {
    lexer.EqualToken: "beq",
    # lexer.NotEqualToken: "NotImplemented",
    # lexer.GreaterThanToken: "NotImplemented",
    # lexer.SmallerThanToken: "NotImplemented",
    lexer.GreaterOrEqualToken: "bge",
    # lexer.SmallerOrEqualToken: "NotImplemented",
}
