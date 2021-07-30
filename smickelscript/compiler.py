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


class AsmData:
    def __init__(self, literal_values=None, stack=None):
        self.literal_values = literal_values or {}
        self.stack = stack or []


def compile_source(source: str) -> str:
    return compile(parser.load_source(source))


# def compile(ast: List[parser.ParserToken], statement: parser.ParserToken = None, state=None):
#     if statement == None:
#         if not ast or len(ast) == 0:
#             raise SmickelCompilerException("No AST")
#         statement = ast[0]

#     if state == None:
#         state = AsmBuilder()

#     statement_type = type(statement)
#     if statement_type in token_compilers:
#         src, state = token_compilers[statement_type](ast[1:], statement, state)
#     else:
#         raise NotImplementedError(
#             "Statement {} is not implemented.".format(statement_type.__name__)
#         )


def compile(ast: List[parser.ParserToken], data: AsmData = None):
    def declare_variable(name, value):
        # TODO: Currently this only works for string literals
        return f'{name}:\n  .{value[0]} "{value[1]}"'

    if data == None:
        data = AsmData()

    src, data = compile_token(ast[0], data)

    if len(ast) > 1:
        return src + compile(ast[1:], data)

    full_src = ".cpu cortex-m0\n.align 2\n\n.data\n\n"
    full_src += "\n".join([declare_variable(x, data[x]) for x in data])
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
    data = AsmData(data.literal_values.copy(), data.stack[:])

    # Rename main to smickel_main
    func_name = statement.identifier.value
    if func_name == "main":
        func_name = "smickelscript_entry"

    # Link arg names to their registers
    names = [x.identifier.value for x in statement.parameters]
    registers = [f"r{x}" for x in range(0, len(statement.parameters))]
    stack_layer = dict(zip(names, registers))
    data.stack.append(stack_layer)

    body_src, data = compile_scope(statement.body, data)
    src = f"\n{func_name}:\n"
    src += "  push { r4, r5, r6, lr }\n"
    src += body_src
    src += "  pop { r4, r5, r6, pc }\n"
    return src, data


def compile_func_call(statement: parser.FuncCallToken, data: AsmData):
    data = AsmData(data.literal_values.copy(), data.stack[:])

    def compile_push_var(nr, var):
        if type(var.value) == lexer.StringLiteralToken:
            var_name = f"lit_{len(data.literal_values)}"
            data.literal_values[var_name] = ["asciz", var.value.value]
            return f"  ldr r{nr}, ={var_name}\n"
        else:
            raise NotImplementedError()

    if len(statement.args) > 4:
        raise IllegalFunctionCallException("Can't have more than 4 function arguments.")

    src = "\n".join([compile_push_var(k, v) for k, v in enumerate(statement.args)])
    src += f"  bl {statement.identifier.value}\n"
    return src, data


def compile_scope(scope: parser.ScopeWithBody, data: AsmData, counter=0):
    if len(scope.body) <= counter:
        return "", data

    src, data = compile_token(scope.body[counter], data)
    src2, data = compile_scope(scope, data, counter + 1)
    return src + src2, data


def compile_if_statement(statement: parser.IfStatementToken, data: AsmData):
    src_load_lhs, data = compile_load_var("r0", statement.condition.lhs, data)
    src_load_rhs, data = compile_load_var("r1", statement.condition.rhs, data)
    src_condition = "  cmp r0, r1\n"

    # Generate code for true and false bodies
    else_label = "else"

    src_true, data = compile_scope(statement.true_body, data)
    src_body = src_true + "\n"

    if statement.false_body != None:
        src_false, data = compile_scope(statement.false_body, data)
        src_body += f"{else_label}:\n" + src_false + "\n"
    else:
        src_body += f"{else_label}:\n"

    condition_type = type(statement.condition.operator)
    if condition_type in condition_type_map:
        op = condition_type_map[condition_type]
        src = f"  {op} {else_label}\n"

        return src_load_lhs + src_load_rhs + src_condition + src + src_body, data
    else:
        raise NotImplementedError()


def compile_return_statement(statement: parser.ReturnToken, data: AsmData):
    value = get_var_value(statement.value, data)
    # TODO: This `bx lr` probably is not correct. Do we still need to delete the stack or something?
    return f"  mov r0, {value}\n  bx lr\n", data


def compile_load_var(register, var, data: AsmData):
    value = get_var_value(var, data)
    return f"  mov {register}, {value}\n", data


def get_var_value(token: lexer.ValueToken, data: AsmData):
    def get_value(layer):
        if token.value in layer:
            # TODO: Also add in which layer this value is
            return layer[token.value]

    if type(token) == parser.LiteralToken:
        if type(token.value) == lexer.NumberLiteralToken:
            return f"#{token.value.value}"
        elif type(token.value) == lexer.BoolLiteralToken:
            return f"#{1 if token.value.value == 'true' else 0}"
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
    parser.FuncCallToken: compile_func_call,
    parser.IfStatementToken: compile_if_statement,
    parser.ReturnToken: compile_return_statement,
}

# This map should return the operator which does the inverse.
condition_type_map = {
    lexer.EqualToken: "bnq",
    # lexer.NotEqualToken: "NotImplemented",
    # lexer.GreaterThanToken: "NotImplemented",
    # lexer.SmallerThanToken: "NotImplemented",
    # lexer.GreaterOrEqualToken: "NotImplemented",
    # lexer.SmallerOrEqualToken: "NotImplemented",
}

if __name__ == "__main__":
    compile_source("""func main() { println("Hello World"); }""")
