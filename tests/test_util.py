from py4a.util import get_spec_type


def test_get_spec_type():
    test_data = {
        "foo": "any",
        "foo (== 1.0)": "fixed",
        "foo (>=1.0)": "at-least",
        "foo (<= 1.0)": "at-most",
        "foo(>   1.0)": "at-least",
        "foo(  >= 1.0)": "at-least",
        "foo   (~=  1.2)": "var-minor",
        "foo  (~=  1.2.1)": "var-micro",
        "foo (< 0.100.0,>=0.99.0)": "range",
        "foo (<=3.5.0,>=3.1.2)": "range",
        "foo (>=3.1.2,<=3.5.0)": "range",
        "foo (== 1.0, != 2.0)": "other",
    }
    for k, v in test_data.items():
        print(k, v)
        assert get_spec_type(k) == v
