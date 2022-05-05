import ast
import py4a.api.static as static
import py4a.api.entity as entity

from typing import Type, Callable


test_code1 = """
@lrucache(maxsize=128)
def f(a: int = 1, b: str = "2") -> int:
    return a + int(b)
"""
test_code2 = """
@decorator1
@decorator2
def f(a: "annotation", /, b=1, c=2, *d, e: Type, f=k, **g) -> "return annotation":
    pass
"""
test_code3 = "async def f(): await other_func()"
class_code = """
@decorator1
class A(object):
    A = 1
    B: str = "abc"
    def __init__(self, a: int = 1, b: str = "2"):
        self.a = a
        self.b = b
    def f(self, c: int = 3) -> str:
        return A + self.b + self.c
    class Inner():
        def __init__(self, i: int = 1):
            self.i = i
"""
mixed_code = """
CONST = 0
def foo(a: str, b: int) -> int:
    def foo2(c: str) -> int: # Should not be parsed
        return a + c
    d = 2
    return int(a) + b + foo2(d)
class Bar(object):
    CLASS_CONST = 2
    def __init__(self, a: str, b: str):
        self.a = a
        self.b = b
    def foo(self) -> str:
        return self.a + self.b
    @staticmethod
    def static():
        return "abc"
    class Inner(Bar):
        pass
"""


def load(
    code: str, node_type: Type[ast.AST], return_func: Callable[[ast.AST], entity.Entity]
):
    tree = ast.parse(code, type_comments=True)
    for node in ast.walk(tree):
        if isinstance(node, node_type):
            ret = return_func(node)
            print(f"Scanning {node_type} and load using {return_func}:")
            print(code)
            print("Results: ", ret)
            return ret


def test_get_api_entities():
    tree = ast.parse(mixed_code, type_comments=True)
    entities = static.get_api_entities(tree)
    print(entities)
    assert len(entities) == 3
    assert isinstance(entities[0], entity.Variable) and entities[0].name == "CONST"
    assert isinstance(entities[1], entity.Function) and entities[1].name == "foo"
    assert isinstance(entities[2], entity.Class) and entities[2].name == "Bar"
    assert entities[2].static_fields[0].name == "CLASS_CONST"
    assert entities[2].fields[0].name == "a"
    assert entities[2].fields[1].name == "b"
    assert entities[2].methods[0].name == "__init__"
    assert entities[2].methods[1].name == "foo"
    assert entities[2].methods[2].name == "static"
    assert entities[2].classes[0].name == "Inner"
    assert entities[2].classes[0].bases == ["Bar"]


def test_convert_arguments():
    arguments = load(
        test_code2, ast.FunctionDef, lambda node: static._convert_arguments(node.args)
    )

    assert isinstance(arguments, list)
    assert len(arguments) == 7

    # Check names
    assert arguments[0].name == "a"
    assert arguments[3].name == "d"

    # Check flags
    for arg in arguments:
        assert arg.pos_only + arg.kw_only + arg.vararg + arg.kwarg <= 1
    assert arguments[0].pos_only and arguments[6].kwarg

    # Check default values
    assert (
        arguments[1].default == "1"
        and arguments[2].default == "2"
        and arguments[5].default == "k"
    )

    # Check type
    assert arguments[4].type == "Type"


def test_convert_function():
    func = load(test_code1, ast.FunctionDef, static._convert_function)
    # Handle complex method definition
    assert func.returns == "int"
    assert func.name == "f"
    assert len(func.args) == 2
    assert not func.is_async
    assert (
        func.args[0].name == "a"
        and ast.literal_eval(func.args[0].default) == 1
        and func.args[0].type == "int"
    )
    assert (
        func.args[1].name == "b"
        and ast.literal_eval(func.args[1].default) == "2"
        and func.args[1].type == "str"
    )

    # Should show signature
    assert (
        "@lrucache(maxsize=128) def f(a: int = 1, b: str = '2') -> int"
        == func.signature
    )

    # Should handle decorators
    func = load(test_code2, ast.FunctionDef, static._convert_function)
    assert func.decorators == ["decorator1", "decorator2"]
    assert not func.is_async

    assert (
        "@decorator1 @decorator2 def f(a: 'annotation', /, b = 1, c = 2, *d, e: Type, f = k, **g) -> 'return annotation'"
        == func.signature
    )

    # Should handle async functions
    func = load(test_code3, ast.AsyncFunctionDef, static._convert_function)
    assert func.is_async


def test_convert_field():
    # Should work on common field declarations
    vars = load("a: int = 4", ast.AnnAssign, static._convert_variables)
    assert (
        vars[0].name == "a"
        and ast.literal_eval(vars[0].value) == 4
        and vars[0].type == "int"
    )
    vars = load("CONST = 'abc'", ast.Assign, static._convert_variables)
    assert (
        vars[0].name == "CONST"
        and ast.literal_eval(vars[0].value) == "abc"
        and vars[0].type is None
    )

    # Should handle chains
    vars = load("a = b = c", ast.Assign, static._convert_variables)
    assert vars[0].name == "a" and vars[0].value == "c"
    assert vars[1].name == "b" and vars[1].value == "c"

    # Should not handle such assign statements
    vars = load("A: int", ast.AnnAssign, static._convert_variables)
    assert len(vars) == 0
    vars = load("ast.c = 21", ast.Assign, static._convert_variables)
    assert len(vars) == 0

    # Should handle tuples and list
    vars = load("a, b = 3, 'abc'", ast.Assign, static._convert_variables)
    assert vars[0].name == "a" and ast.literal_eval(vars[0].value) == 3
    assert vars[1].name == "b" and ast.literal_eval(vars[1].value) == "abc"
    vars = load("a, b, c.d = [1, 2, 3]", ast.Assign, static._convert_variables)
    assert len(vars) == 2
    assert vars[0].name == "a" and ast.literal_eval(vars[0].value) == 1
    assert vars[1].name == "b" and ast.literal_eval(vars[1].value) == 2
    assert all(f.type is None for f in vars)
    vars = load("a, b = c", ast.Assign, static._convert_variables)
    assert vars[0].name == "a" and vars[0].value == "c[0]"
    assert vars[1].name == "b" and vars[1].value == "c[1]"

    # A complex case
    vars = load("a, b = c, d = 1, e", ast.Assign, static._convert_variables)
    assert len(vars) == 4
    expected_names = ["a", "b", "c", "d"]
    expected_values = ["1", "e", "1", "e"]
    for i in range(len(vars)):
        assert vars[i].name == expected_names[i]
        assert vars[i].value == expected_values[i]


def test_convert_class():
    cls = load(class_code, ast.ClassDef, static._convert_class)
    assert cls.name == "A"
    assert cls.static_fields[0].name == "A"
    assert cls.static_fields[1].name == "B"
    assert cls.fields[0].name == "a"
    assert cls.fields[1].name == "b"
    assert cls.methods[0].name == "__init__"
    assert cls.methods[1].name == "f"
    assert cls.classes[0].name == "Inner"
    assert cls.decorators == ["decorator1"]
