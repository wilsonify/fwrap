#!/usr/bin/python
import glob
import logging
import os, sys, re, shutil, unittest, doctest
from collections import namedtuple

import pytest

from fwrap.fwrapc import fwrapc, call_waf
from fwrap.fwrapper import wrap

current_dir = os.path.abspath(os.path.dirname(__file__))
logging.debug(f"current_dir = {current_dir}")
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
logging.debug(f"parent_dir = {parent_dir}")


def test_handle_directory():
    for filename in glob.glob(f"{current_dir}/run/*.f*", recursive=True):
        print(f"filename = {filename}")


@pytest.mark.parametrize(
    ("filepath", "expected"), (
            (f"{current_dir}/compile/cmplx_array.f90", True),
            (f"{current_dir}/compile/many_args.f90", True),
            (f"{current_dir}/compile/old_decl.f90", True),
            (f"{current_dir}/compile/all_char.f90", True),
            (f"{current_dir}/compile/py_kw_arg.f90", True),
            (f"{current_dir}/compile/int_args.f90", True),
            (f"{current_dir}/compile/simple_array.f90", True),
            (f"{current_dir}/compile/char_args.f90", True),
    )
)
def test_compile(filepath, expected):
    base, ext = os.path.splitext(filepath)
    base_head, base_tail = os.path.split(base)
    wrap(
        sources=filepath,
        name=f"{base_tail}_ext"
    )
    pyx_path = f"{current_dir}/{base_tail}_ext.pyx"

    assert os.path.isfile(pyx_path)

    for generated in glob.glob(f"{base_tail}_ext*"):
        os.remove(generated)  # cleanup


@pytest.mark.parametrize(
    ("filepath", "expected"), (
            (f"{current_dir}/run/dim_expr.f90", True),
            (f"{current_dir}/run/func_returns.f90", True),
            (f"{current_dir}/run/default_types.f90", True),
            (f"{current_dir}/run/all_logical_arrays.f90", True),
            (f"{current_dir}/run/array_intents.f90", True),
            (f"{current_dir}/run/all_ints.f90", True),
            (f"{current_dir}/run/old_decl.f90", True),
            (f"{current_dir}/run/all_logicals.f90", True),
            (f"{current_dir}/run/all_complex_arrays.f90", True),
            (f"{current_dir}/run/all_char.f90", True),
            (f"{current_dir}/run/char_array.f90", True),
            (f"{current_dir}/run/all_complex.f90", True),
            (f"{current_dir}/run/int_args.f90", True),
            (f"{current_dir}/run/all_reals.f90", True),
            (f"{current_dir}/run/all_real_arrays.f90", True),
            (f"{current_dir}/run/all_integer_arrays.f90", True),
            (f"{current_dir}/run/array_types.f90", True),
            (f"{current_dir}/run/ndims.f90", True),

    )
)
def test_call_waf(filepath, expected):
    # equivalent to ```fwrapc.py configure build fsrc```
    base, ext = os.path.splitext(filepath)
    base_head, base_tail = os.path.split(base)
    projname = f'{base}_fwrap'
    projdir = os.path.join(base_head, projname)
    Opts = namedtuple("opts", ["name", "outdir"])

    call_waf(
        opts=Opts(
            name=f"{projname}",
            outdir=f"{projdir}"
        ),
        args=[filepath],
        orig_args=["configure", "build"]
    )


@pytest.mark.parametrize(
    ("filepath", "expected"), (
            (f"{current_dir}/run/dim_expr.f90", True),
            (f"{current_dir}/run/func_returns.f90", True),
            (f"{current_dir}/run/default_types.f90", True),
            (f"{current_dir}/run/all_logical_arrays.f90", True),
            (f"{current_dir}/run/array_intents.f90", True),
            (f"{current_dir}/run/all_ints.f90", True),
            (f"{current_dir}/run/old_decl.f90", True),
            (f"{current_dir}/run/all_logicals.f90", True),
            (f"{current_dir}/run/all_complex_arrays.f90", True),
            (f"{current_dir}/run/all_char.f90", True),
            (f"{current_dir}/run/char_array.f90", True),
            (f"{current_dir}/run/all_complex.f90", True),
            (f"{current_dir}/run/int_args.f90", True),
            (f"{current_dir}/run/all_reals.f90", True),
            (f"{current_dir}/run/all_real_arrays.f90", True),
            (f"{current_dir}/run/all_integer_arrays.f90", True),
            (f"{current_dir}/run/array_types.f90", True),
            (f"{current_dir}/run/ndims.f90", True),

    )
)
def test_fwrapc(filepath, expected):
    # equivalent to ```fwrapc.py configure build fsrc```
    base, ext = os.path.splitext(filepath)
    base_head, base_tail = os.path.split(base)
    projname = f'{base}_fwrap'
    projdir = os.path.join(base_head, projname)
    fwrapc(argv=[
        filepath,
        "--configure",
        "--build",
        f"--name={projname}",
        f"--outdir={projdir}"
    ])
    assert filepath == expected
