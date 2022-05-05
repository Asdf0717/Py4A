import ast
import py4a.api.entity as entity
import py4a.api.static as static
import py4a.client.analyzer as analyzer

from pprint import pprint


with open("tests/resource/test_client.py", "r") as f:
    code1 = ast.parse(f.read())
with open("tests/resource/test_client2.py", "r") as f:
    code2 = ast.parse(f.read())


def test_client1():
    visitor = analyzer._SourceVisitor()
    visitor.visit(code1)
    pprint(sorted(visitor.calls))
    pprint(visitor.aliases)
    calls = [
        "os",
        "pd",
        "deque",
        "defaultdict",
        "z",
        "os.mkdir(*)",
        "pd.read_csv(*)",
        "df.head(*)",
        "deque(*)",
        "x.append(*)",
        "defaultdict()",
        "z(*)",
    ]
    aliases = {
        "pd": {"pandas"},
        "deque": {"collections.deque"},
        "defaultdict": {"collections.defaultdict"},
        "z": {"sys.exit"},
        "df": {"pd.read_csv(*)", "pd.DataFrame()"},
        "x": {"deque(*)"},
        "y": {"defaultdict()"},
    }
    for c in calls:
        assert c in visitor.calls
    for a in aliases:
        assert a in visitor.aliases
    access_chains = {str(x) for x in analyzer.get_api_access_chains(code1)}
    pprint(sorted(access_chains))
    accesses = {
        "os.mkdir(*):9",
        "pandas.read_csv(*):10",
        "pandas.DataFrame():11",
        "pandas.DataFrame().head(*):12",
        "collections.deque(*):13",
        "collections.deque(*).append(*):14",
        "collections.defaultdict():15",
        "sys.exit(*):17",
    }
    for c in accesses:
        assert c in access_chains


def test_source_visitor2():
    visitor = analyzer._SourceVisitor()
    visitor.visit(code2)
    pprint(sorted(visitor.calls))
    pprint(visitor.aliases)
    access_chains = {str(x) for x in analyzer.get_api_access_chains(code2)}
    pprint(sorted(access_chains))
    accesses = {
        "a.foo():16",
        "b.bar(*):16",
        # TODO: Line number may be wrong due to ambiguities in alias resolution
        "c1.c2():3,10,12,19",
        "c1.c3():4,11,12",
        "d1.d2.d1(*,*):16",
        "d1.d2.d2(...,**):19",
    }
    for c in accesses:
        assert c in access_chains


def test_call_match():
    code = """def f(): pass"""
    func = static._convert_function(ast.parse(code).body[0])
    print(func.signature)

    call = analyzer.AccessChain._from_str("f()").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(a=*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(**)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(^^^)").chain[0]
    assert call.match(func)[0] is True

    code = """def f(**kwargs): pass"""
    func = static._convert_function(ast.parse(code).body[0])
    print(func.signature)

    call = analyzer.AccessChain._from_str("f()").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(a=*)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(**)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(^^^)").chain[0]
    assert call.match(func)[0] is True

    code = """def f(a, b, c, d=3, e=4, f=6): pass"""
    func = static._convert_function(ast.parse(code).body[0])
    print(func.signature)

    call = analyzer.AccessChain._from_str("f(*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(*,*,*)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*,*,*,*,*,*)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*,*,*,*,*,*,*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(*,^^^)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(**)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*,*,a=*,**)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(k=*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(a=*,b=*,c=*)").chain[0]
    assert call.match(func)[0] is True

    code = """def f(a: "annotation", /, b=1, c=2, *d, e: Type, f=k, **g) -> "return annotation": pass"""
    func = static._convert_function(ast.parse(code).body[0])
    print(func.signature)

    call = analyzer.AccessChain._from_str("f(*)").chain[0]
    assert call.match(func)[0] is False
    call = analyzer.AccessChain._from_str("f(*,*,*,e=*)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*,*,*,*,e=*)").chain[0]
    assert call.match(func)[0] is True
    call = analyzer.AccessChain._from_str("f(*,*,^^^,e=*)").chain[0]
    assert call.match(func)[0] is True


def test_access_chain_match():
    packages = static.get_apis_from_wheel(
        "pandas",
        "tests/resource/pandas-1.3.2-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    )
    packages = {p.name: p for p in packages}

    print(packages["pandas"].get("pandas.read_csv").signature)

    access_chains = analyzer.get_api_access_chains(code1)
    for chain in access_chains:
        if chain.top_level == "pandas":
            print(chain)
            match_result = chain.match(packages)
            print(match_result)
            assert match_result.status == analyzer.MatchStatus.MATCH

    access_chains2 = analyzer.get_api_access_chains(code1, ["pandas"])
    print(access_chains2)
    for chain in access_chains2:
        assert str(chain).startswith("pandas")

