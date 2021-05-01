# ------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
# ------------------------------------------------------------------------------

from fwrap.fort_expr import parse, ExtractNames
import pytest


def test_signed_int_lit():
    istr = str(310130813080138)
    s = "+%s" % istr
    skp = "%s_8 + 10_abc" % s
    assert skp == "+310130813080138_8 + 10_abc"


def test_func_ref():
    ss = "foo(a, b-3+x(14), c=d+1)"
    expr = parse(ss)
    assert expr == "foo"


def test_extractnames():
    ss = "-+12354.5678E-12_aoeu"
    expr = parse(ss)
    xtor = ExtractNames()
    xtor.visit(expr)
    assert xtor.names == ['aoeu']

    ss2 = ".02808_a123_45"
    expr = parse(ss2)

    xtor = ExtractNames()
    xtor.visit(expr)
    assert xtor.names == ['a123_45']

    funccall = parse("foo(a, b-3+x(14), c=d+1)")
    xtor = ExtractNames()
    xtor.visit(funccall)
    assert xtor.names == ['a', 'b', 'd']
    assert xtor.funcnames == ['foo', 'x']

    power = parse("+1**2_a8")
    xtor = ExtractNames()
    xtor.visit(power)
    eq_(xtor.names, ['a8'])
    eq_(xtor.funcnames, [])


def test_char_lit_const():
    clc2 = parse("aoeu_'1202\"04''028'").subexpr[0]
    clc3 = parse('1_"as ""onthu\'sanetu"').subexpr[0]
    eq_(clc2.kind.param.name, 'aoeu')
    eq_(clc2.string, '1202"04\'028')
    eq_(clc3.kind.param.digit_string, '1')
    eq_(clc3.string, 'as "onthu\'sanetu')


@pytest.mark.parametrize(
    ("tstr", "res", "funcs"), (
            ("9", [], []),
            ("-9", [], []),
            ("3.1415926", [], []),
            ("3.1415926E10", [], []),
            ("3.1415926_8", [], []),
            ("--9", [], []),
            ("-E", ['E'], []),
            ("9 + 3 + 6", [], []),
            ("9 + 3 / 11", [], []),
            ("(9 + 3)", [], []),
            ("(9+3) / 11", [], []),
            ("9 - 12 - 6", [], []),
            ("9 - (12 - 6)", [], []),
            ("2*3.14159", [], []),
            ("3.1415926535*3.1415926535 / 10", [], []),
            ("PI * PI / 10", ["PI", "PI"], []),
            ("PI*PI/10", ["PI", "PI"], []),
            ("PI**2", ["PI"], []),
            ("round(PI**2)", ["PI"], ["round"]),
            ("6.02E23 * 8.048", [], []),
            ("e / 3", ["e"], []),
            ("sin(PI/2)", ['PI'], ["sin"]),
            ("trunc(E)", ['E'], ["trunc"]),
            ("trunc(-E)", ['E'], ["trunc"]),
            ("round(E)", ['E'], ["round"]),
            ("round(-E)", ['E'], ["round"]),
            ("E**PI", ['E', 'PI'], []),
            ("2**3**2", [], []),
            ("2**3+2", [], []),
            ("2**3+5", [], []),
            ("2**9", [], []),
            ("sgn(-2)", [], ["sgn"]),
            ("sgn(0)", [], ["sgn"]),
            ("sgn(0.1)", [], ["sgn"]),
            ("(0.0)", [], []),
            ("(abc, def)", ['abc', 'def'], []),
            ("(0.0, 0.0)", [], []),
            ("3 -(-(+9))", [], []),
            ("3 -(-(+(-(-(+9)))))", [], []),
            ("kind('a')", [], ["kind"]),
            ("(123456_'aosentuh' // aoeu_'aosnteh')", ['aoeu'], []),
            ("(0.0_r8, 1.0_d12)", ["r8", "d12"], []),
            ("1234.567E12_g_1 + .35009_f13_ / (-.9D3_D__3 + 1._a1)", ['g_1', 'f13_', 'D__3', 'a1'], []),
            ("*", [], []),
            ("", [], []),
    )
)
def test_tester(tstr, res, funcs):
    expr = parse(tstr)
    xtor = ExtractNames()
    xtor.visit(expr)
    assert xtor.names == res
    assert xtor.funcnames == funcs


@pytest.mark.parametrize(
    ("tstr", "res", "funcs"), (
            ("(1.0E+0, 0.0E+0)", [], []),
            ("(1.0D+0, 0.0D+0)", [], []),
            ("(-1.0D+00, 0.0D+00)", [], []),
    )
)
def test_regr_reallitconst(tstr, res, funcs):
    expr = parse(tstr)
    xtor = ExtractNames()
    xtor.visit(expr)
    assert xtor.names == res
    assert xtor.funcnames == funcs
