import random
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


class VariableAlreadyExistsException(SmickelCompilerException):
    """Thrown when a variable is defined which already exists."""

    pass


class EntrypointNotFoundException(SmickelCompilerException):
    """Thrown when no main function is found."""

    pass


class AsmData:
    def __init__(self, data=None, stack=None):
        self.data = data or {}
        self.stack = stack or []


def compile_file(file: str) -> str:
    asm = compile_ast(parser.load_file(file))

    if "smickelscript_codegen_main:" not in asm:
        raise EntrypointNotFoundException("Main function not found.")

    return asm


def compile_src(source: str) -> str:
    asm = compile_ast(parser.load_source(source))

    if "smickelscript_codegen_main:" not in asm:
        raise EntrypointNotFoundException("Main function not found.")

    return asm


def compile_ast(ast: List[parser.ParserToken], data: AsmData = None):
    def declare_variable(name, value):
        return f"{name}: .{value[0]} {value[1]}"

    if len(ast) == 0:
        return []

    if data == None:
        data = AsmData()

    src, data = compile_token(ast[0], data)

    if len(ast) > 1:
        return compile_ast(ast[1:], data) + src

    full_src = ".cpu cortex-m0\n.align 2\n"

    if len(data.data) > 0:
        full_src += "\n.data\n\n"
        full_src += "\n".join([declare_variable(x, data.data[x]) for x in data.data])
        full_src += "\n"

    full_src += "\n.text\n"
    full_src += ".global smickelscript_codegen_main, smickelscript_codegen_randinit\n"
    full_src += "\nsmickelscript_codegen_randinit:\n"
    full_src += "  push { lr }\n"
    full_src += f"  mov r0, #{random.getrandbits(8)}\n"
    full_src += "  bl srand\n"
    full_src += "  pop { pc }\n"
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

    func_name = statement.identifier.value
    if func_name == "main":
        # Rename main to smickel_main
        func_name = "smickelscript_codegen_main"

        if len(statement.parameters) > 0:
            raise SmickelCompilerException(
                "The main function is not allowed to have any parameters."
            )

    if len(statement.parameters) > 1:
        raise SmickelCompilerException(
            "Error on line {}. Function {} can't have more than 1 parameters.".format(
                statement.identifier.line_nr, statement.identifier.value
            )
        )

    # Link parameter names to their registers
    # Function parameter will be saved in r3 register
    # This could be changed to allow for more registers, but that'd also require changes
    # in other places. I can't really be bothered to support it, so for now you are only
    # allowed to pass one parameter to a function.
    names = [x.identifier.value for x in statement.parameters]
    registers = [f"r{x+3}" for x in range(0, len(statement.parameters))]
    stack_layer = dict(zip(names, registers))
    data.stack.append(stack_layer)

    body_src, data = compile_scope(statement.body, data, True)
    src = f"\n@ Function {statement.identifier.value} on line {statement.identifier.line_nr}\n"
    src += f"{func_name}:\n"
    src += body_src

    # Also remove the stack layer
    data.stack = data.stack[:-1]

    return src, data


def compile_func_call(token: parser.FuncCallToken, data: AsmData):
    data = AsmData(data.data.copy(), data.stack[:])

    def compile_push_var(nr, var):
        if type(var) in [
            parser.OperatorToken,
            parser.FuncCallToken,
            lexer.IdentifierToken,
            parser.IndexAccessToken,
        ]:
            return compile_token(var, data)[0]
        elif type(var.value) == lexer.StringLiteralToken:
            var_name = f"lit_{len(data.data)}"
            data.data[var_name] = ["asciz", f'"{var.value.value}"']
            dbg = f"  @ Loading variable ({nr}, {type(var.value).__name__}) on line {var.value.line_nr}\n"
            return dbg + f"  ldr r{nr}, ={var_name}\n"
        else:
            dbg = f"  @ Loading variable ({nr}, {type(var.value).__name__}) on line {var.value.line_nr}\n"
            src, _ = compile_literal(var, data, f"r{nr}")
            return dbg + src

    if len(token.args) > 1:
        raise IllegalFunctionCallException("Can't have more than 1 function arguments.")

    func_name = token.identifier.value

    # Rename some built in functions because we want to use our own implementation, and not the Arduino implementation.
    if func_name in ["rand", "time", "time_ms"]:
        func_name = "smickelscript_" + func_name

    src = f"  @ Function call to {func_name} on line {token.identifier.line_nr}\n"
    src += "\n".join([compile_push_var(k, v) for k, v in enumerate(token.args)])
    src += f"  bl {func_name}\n"
    return src, data


def compile_literal(token: parser.LiteralToken, data: AsmData, register="r0"):
    value_type = type(token.value)
    if value_type == lexer.BoolLiteralToken:
        return f"  mov {register}, #{1 if token.value.value == 'true' else 0}\n", data
    elif value_type == lexer.NumberLiteralToken:
        if int(token.value.value) < 256:
            return f"  mov {register}, #{token.value.value}\n", data
        return f"  ldr {register}, ={token.value.value}\n", data
    elif value_type == lexer.StringLiteralToken:
        # Unescape values
        value = bytes(token.value.value, "utf-8").decode("unicode_escape")

        if len(value) > 1:
            raise SmickelCompilerException(
                "Error on line {}. Only char literals are supported.".format(token.value.line_nr)
            )
        dbg = f"  @ Character literal '{token.value.value}'\n"
        return dbg + f"  mov {register}, #'{token.value.value}'\n", data

    # Trash code
    line_nr = token.line_nr if hasattr(token, "line_nr") else token.value.line_nr

    raise NotImplementedError(
        "Error on line {}. Literal of type {} is not implemented.".format(
            line_nr, value_type.__name__
        )
    )


def compile_scope(scope: parser.ScopeWithBody, data: AsmData, create_stack_layer=False, counter=0):
    src = ""
    pop_src = "  pop { r4, r5, r6, pc }\n"

    if create_stack_layer and counter == 0:
        # Push registers we are not allowed to change to the stack.
        # Also moves the r0 register (function parameter) to the r3 register,
        # we do this because some instructions change the r0 register which
        # would cause us to lose our parameter value.
        src += "  push { r4, r5, r6, lr }\n  mov r3, r0\n"

    if len(scope.body) <= counter:
        if create_stack_layer:
            if counter > 0:
                return pop_src, data
            else:
                return "  @ Empty function\n  mov pc, lr\n", data
        else:
            return "", data

    src_token, data = compile_token(scope.body[counter], data)
    src_rest, data = compile_scope(scope, data, create_stack_layer, counter + 1)

    # Don't add duplicate pop statements when not needed
    if src_rest == pop_src and src_token.endswith(pop_src):
        return src + src_token, data
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
    elif type(token.operator) == lexer.SubtractionToken:
        src_condition = f"  sub {dst_register}, r0, r1\n"
    elif type(token.operator) == lexer.AdditionToken:
        src_condition = f"  add {dst_register}, r0, r1\n"
    elif type(token.operator) == lexer.ModuloToken:
        # This is cheating, but modulo is complicated.
        src_condition = f"  bl smickelscript_modulo\n"
        if dst_register != "r0":
            src_condition += f"  mov {dst_register}, r0\n"
    elif type(token.operator) == lexer.MultiplicationToken:
        # Destination register **must** be r0 or r1
        if dst_register in ["r0", "r1"]:
            src_condition = f"  mul {dst_register}, r0, r1\n"
        else:
            src_condition = f"  mul r0, r0, r1\n"
            src_condition += f"  mov {dst_register}, r0\n"
    else:
        raise NotImplementedError(
            "Error on line {}. Operator '{}' is not implemented.".format(
                token.operator.line_nr, token.operator
            )
        )
    dbg = f"  @ {str(token.operator).replace('Token', '')} on line {token.operator.line_nr}\n"
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

    data = AsmData(data.data.copy(), data.stack[:])

    # Static variables are saved in the `.DATA` segment, other variables on the stack.
    if token.static:
        if token.identifier.value in data.data:
            raise VariableAlreadyExistsException(
                "Error on line {}. A variable with the identifier {} already exists.".format(
                    token.identifier.line_nr, token.identifier.value
                )
            )

        if type(token.value) == parser.FixedSizeArrayToken:
            array_size = int(token.value.size.value.value)

            if token.value.init_value == None:
                value = ["0"] * array_size
            else:
                if (
                    type(token.value.init_value) != parser.LiteralToken
                    or type(token.value.init_value.value) != lexer.StringLiteralToken
                ):
                    raise SmickelCompilerException("Array initial value must be a string literal.")

                value = [f"'{x}'" for x in token.value.init_value.value.value]
                padding_len = array_size - len(value)
                value += ["0"] * padding_len

            value = ", ".join(value)
            data.data[token.identifier.value] = ["word", value]
            return "", data

        if type(token.value) == parser.FuncCallToken:
            data.data[token.identifier.value] = ["word", "0"]
            src, data = compile_func_call(token.value, data)

            # Write the result to the .data section (at runtime).
            src += f"  ldr r1, ={token.identifier.value}\n"
            src += "  str r0, [ r1 ]\n"
            dbg = f"  @ Init static variable '{token.identifier.value}' with result from function call to '{token.value.identifier.value}' on line {token.identifier.line_nr}\n"
            return dbg + src, data

        if type(token.value) != parser.LiteralToken:
            raise NotImplementedError(
                "Error on line {}. This behavior is not implemented.".format(
                    token.identifier.line_nr
                )
            )

        if type(token.value.value) == lexer.StringLiteralToken:
            data.data[token.identifier.value] = ["asciz", f'"{token.value.value.value}"']
        elif type(token.value.value) == lexer.NumberLiteralToken:
            data.data[token.identifier.value] = ["long", token.value.value.value]
        else:
            raise NotImplementedError(
                "Error on line {}. Value type {} is not implemented.".format(
                    token.identifier.line_nr, token.value.value
                )
            )

        return "", data
    else:
        if type(token.value) == parser.FixedSizeArrayToken:
            raise SmickelCompilerException(
                "Error on line {}. Arrays need to be static.".format(token.identifier.line_nr)
            )

        if len(data.stack[-1]) == 4:
            raise SmickelCompilerException("Variable limit reached.")

        # Figure out where to save the variable
        reg = f"r{4 + len(data.stack[-1])}"
        data.stack[-1][token.identifier.value] = reg

        if type(token.value) == parser.IndexAccessToken:
            src, data = compile_array_access(token.value, data, reg)
            dbg_value_name = f"{token.value.identifier.value}[{token.value.index.value}]"
            dbg = f"  @ Init variable '{token.identifier.value}' with value '{dbg_value_name}' on line {token.identifier.line_nr}\n"
        elif type(token.value) == parser.FuncCallToken:
            src, data = compile_func_call(token.value, data)

            # Move result to the correct register
            if reg != "r0":
                src += f"  mov {reg}, r0\n"

            dbg = f"  @ Init variable '{token.identifier.value}' with result from function call to '{token.value.identifier.value}' on line {token.identifier.line_nr}\n"
        else:
            src, data = compile_literal(token.value, data, reg)
            # `token.value.value.value` tragic code :(
            dbg = f"  @ Init variable '{token.identifier.value}' with value '{token.value.value.value}' on line {token.identifier.line_nr}\n"

        return dbg + src, data


def compile_while(token: parser.WhileStatementToken, data: AsmData):
    while_label = "while_" + secrets.token_hex(5)
    while_cond_label = while_label + "_cond"
    while_end_label = while_label + "_end"

    body_src, data = compile_scope(token.body, data)

    if type(token.condition) == parser.LiteralToken:
        if token.condition.value.value != "true":
            raise SmickelCompilerException(
                "Error on line {}. Not supported.".format(token.condition.value.line_nr)
            )

        src = f"  @ While(true) statement on line {token.condition.value.line_nr}\n"
        src += while_label + ":\n"
        src += body_src
        src += f"  b {while_label}\n"
        return src, data
    else:
        line_nr = token.condition.operator.line_nr
        condition_src, data = compile_operator(token.condition, data)

        condition_type = type(token.condition.operator)
        if condition_type in condition_type_map:
            op = condition_type_map[condition_type]
            src_jump_true = f"  {op} {while_label}\n"

            src = f"  @ While statement on line {line_nr}\n"

            # Check if condition is true before running the body.
            src += while_cond_label + ":\n"
            src += condition_src
            src += src_jump_true
            src += f"  b {while_end_label}\n"

            src += while_label + ":\n"
            src += body_src
            src += f"  b {while_cond_label}\n"
            src += while_end_label + ":\n"

            return src, data
    raise NotImplementedError(
        "Error on line {}. Condition '{}' is not implemented.".format(
            line_nr, condition_type.__name__
        )
    )


def compile_assign_var(token: parser.AssignVariableToken, data: AsmData):
    data = AsmData(data.data.copy(), data.stack[:])

    # Figure out where to store the result
    if token.identifier.value in data.stack[-1]:
        reg = data.stack[-1][token.identifier.value]
        store_in_data = False
    elif token.identifier.value in data.data:
        reg = "r0"
        store_in_data = True
    else:
        raise SmickelCompilerException(
            "Variable '{}' not found. Keep in mind that assigning variables in a higher stack layer is currently not supported.".format(
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
        if reg != "r0":
            src += f"  mov {reg}, r0\n"

    if store_in_data:
        src += f"  @ Storing result in static variable '{token.identifier.value}'\n"
        src += f"  ldr r1, ={token.identifier.value}\n"
        src += "  str r0, [ r1 ]\n"

    return src, data


def compile_identifier(token: lexer.IdentifierToken, data: AsmData):
    src, value = get_var_value(token, data)
    # Only move value to r0 if it isn't already in r0
    mov = "" if value == "r0" else f"  mov r0, {value}\n"
    return src + mov, data


def compile_load_var(register, var, data: AsmData):
    if not hasattr(var, "value"):
        raise NotImplementedError("Unsupported value.")

    # Shitty workaround for immediate values above 255
    if type(var.value) == lexer.NumberLiteralToken and int(var.value.value) > 255:
        return f"  ldr {register}, ={var.value.value}\n", data

    src, value = get_var_value(var, data)
    return src + f"  mov {register}, {value}\n", data


def compile_array_insert(token: parser.ArrayInsertToken, data: AsmData):
    # Used registers:
    # r0 = ptr where to store the result
    # r1 = the value to store
    # r2 = the offset inside the array
    #
    # C example:
    #   r0[r2] = r1

    # Evaluate the index (inside the array), this can be a number literal, or a calculated value.
    src, data = compile_token(token.array.index, data)

    # Multiply by 4 because all arrays have WORD sized elements (aka 4 bytes).
    src += "  mov r2, #4\n"
    src += "  mul r2, r0, r2\n"

    # Evaluate the value whose result we want to store.
    # src_value, data = compile_literal(token.value, data, "r1")
    # src += src_value

    src_value, data = compile_token(token.value, data)

    # Move r2 someplace safe if the src_value touches our r2.
    if "r2" in src_value:
        src += "  mov r8, r2\n"
        src += src_value
        src += "  mov r2, r8\n"
    else:
        src += src_value

    # Move our src_value return value to r1
    src += "  mov r1, r0\n"

    # Load array ptr and store result at the given offset.
    src += f"  ldr r0, ={token.array.identifier.value}\n"
    src += "  str r1, [ r0, r2 ]\n"

    dbg = f"  @ Array insertion on line {token.array.identifier.line_nr}\n"
    return dbg + src, data


def compile_array_access(token: parser.IndexAccessToken, data: AsmData, reg="r0"):
    tmp = "r1" if reg != "r1" else "r2"
    src, data = compile_token(token.index, data)
    # Multiply by 4 because all arrays have WORD sized elements (aka 4 bytes).
    src += f"  mov {tmp}, #4\n"
    src += f"  mul r0, r0, {tmp}\n"
    src += f"  ldr {tmp}, ={token.identifier.value}\n"
    src += f"  ldr {reg}, [ r0, {tmp} ]\n"
    return src, data


def get_var_value(token: lexer.ValueToken, data: AsmData):
    def get_value(layer):
        if token.value in layer:
            return "", layer[token.value]
        return None

    if type(token) == parser.LiteralToken:
        if type(token.value) == lexer.NumberLiteralToken:
            return "", f"#{token.value.value}"
        elif type(token.value) == lexer.BoolLiteralToken:
            return "", f"#{1 if token.value.value == 'true' else 0}"
        elif type(token.value) == lexer.StringLiteralToken:
            # Unescape values
            value = bytes(token.value.value, "utf-8").decode("unicode_escape")
            if len(value) > 1:
                raise SmickelCompilerException(
                    "Error on line {}. Only char literals are supported.".format(
                        token.value.line_nr
                    )
                )
            return "", f"#'{token.value.value}'"
        else:
            raise NotImplementedError("Unsupported variable value.")

    # This commented out code could be used if we allow parent stack access, which
    # we don't for now.
    # values = [x for x in map(get_value, data.stack) if x != None]

    # Values in the .DATA segment have priority over local variables.
    if token.value in data.data:
        src = f"  ldr r2, ={token.value}\n"
        src += "  ldr r2, [ r2 ]\n"
        return src, "r2"

    # The compiler only allows you to access variables in the topmost (current) stack layer
    value = get_value(data.stack[-1])

    if value == None:
        raise UndefinedVariableException(
            "Error on line {}. Undefined variable '{}'.".format(token.line_nr, token.value)
        )

    return value


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
    lexer.CommentToken: lambda a, b: ("", b),
    parser.ArrayInsertToken: compile_array_insert,
    parser.IndexAccessToken: compile_array_access,
}

condition_type_map = {
    lexer.EqualToken: "beq",
    lexer.NotEqualToken: "bne",
    lexer.GreaterThanToken: "bgt",
    lexer.SmallerThanToken: "blt",
    lexer.GreaterOrEqualToken: "bge",
    lexer.SmallerOrEqualToken: "ble",
}
