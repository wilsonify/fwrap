# ------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
# ------------------------------------------------------------------------------

# encoding: utf-8
import logging
import os, sys, shutil
import subprocess
import argparse
from collections import namedtuple
from optparse import OptionParser, OptionGroup

PROJECT_OUTDIR = 'fwproj'
PROJECT_NAME = PROJECT_OUTDIR

current_dir = os.path.abspath(os.path.dirname(__file__))
logging.debug(f"current_dir = {current_dir}")
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
logging.debug(f"parent_dir = {parent_dir}")


def setup_dirs(dirname):
    """
    set up the project directory.
    cp waf and wscript into the project dir.
    """
    fwrap_path = os.path.abspath(os.path.dirname(__file__))
    src_dir = os.path.join(dirname, 'src')
    waf_path = os.path.join(fwrap_path, "waf", 'waf-light')
    waf_lib_path = os.path.join(fwrap_path, "waf", 'waflib')
    fw_wscript = os.path.join(fwrap_path, 'fwrap_wscript')
    wscript_path = os.path.join(dirname, 'wscript')

    logging.debug(f"fwrap_path = {fwrap_path}")
    logging.debug(f"src_dir = {src_dir}")
    logging.debug(f"waf_path = {waf_path}")
    logging.debug(f"fw_wscript = {fw_wscript}")
    logging.debug(f"wscript_path = {wscript_path}")

    os.makedirs(dirname, exist_ok=True)
    os.makedirs(src_dir, exist_ok=True)
    shutil.copy(src=fw_wscript, dst=wscript_path)
    shutil.copy(src=waf_path, dst=dirname)
    shutil.copytree(src=waf_lib_path, dst=f"{dirname}/waflib")


def wipe_out(dirname):
    # wipe out everything and start over.
    shutil.rmtree(dirname, ignore_errors=True)


def configure_cb(opts, args, orig_args):
    logging.debug(f"opts.outdir = {opts.outdir}")
    wipe_out(os.path.abspath(opts.outdir))
    setup_dirs(os.path.abspath(opts.outdir))


def build_cb(opts, args, argv):
    srcs = []
    for arg in args:
        larg = arg.lower()
        if larg.endswith('.f') or larg.endswith('.f90'):
            srcs.append(os.path.abspath(arg))

    dst = os.path.join(os.path.abspath(opts.outdir), 'src')
    for src in srcs:
        shutil.copy(src, dst)
    return srcs


def call_waf(opts, args, orig_args):
    configure_cb(opts, args, orig_args)
    srcs = build_cb(opts, args, orig_args)
    py_exe = sys.executable
    waf_path = os.path.join(os.path.abspath(opts.outdir), 'waf-light')
    cmd = [py_exe, waf_path] + orig_args
    os.makedirs(opts.outdir, exist_ok=True)
    os.chdir(os.path.abspath(opts.outdir))
    logging.debug(f"working directory = {os.getcwd()}")
    subprocess.check_call(cmd)


def print_version():
    from fwrap.version import get_version
    vandl = """\
fwrap v%s
Copyright (C) 2010 Kurt W. Smith
Fwrap is distributed under an open-source license.   See the source for
licensing information.  There is NO warranty, not even for MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.
""" % get_version()
    print(vandl)


def fwrapc(argv):
    """
    Main entry point -- called by cmdline script.
    """

    subcommands = ('configure', 'gen', 'build')

    parser = OptionParser()
    parser.add_option('--version', dest="version",
                      action="store_true", default=False,
                      help="get version and license info and exit")

    # configure options
    configure_opts = OptionGroup(parser, "Configure Options")
    configure_opts.add_option("--name",
                              help='name for the extension module [default %default]')
    configure_opts.add_option("--outdir",
                              help='directory for the intermediate files [default %default]')
    parser.add_option_group(configure_opts)

    conf_defaults = dict(name=PROJECT_NAME, outdir=PROJECT_OUTDIR)
    parser.set_defaults(**conf_defaults)

    opts, args = parser.parse_args(args=argv)

    if opts.version:
        print_version()
        return 0

    if not ('configure' in args or 'build' in args):
        parser.print_usage()
        return 1

    return call_waf(opts, args, argv)
