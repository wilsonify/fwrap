from fwrap_src import pyf_iface as pyf
from fwrap_src import fc_wrap
from fwrap_src.code import CodeBuffer

from nose.tools import ok_, eq_, set_trace

class test_empty_func(object):

    def setup(self):
        self.empty_func = pyf.Function(name='empty_func',
                        args=(),
                        return_type=pyf.default_integer)
        self.buf = CodeBuffer()

    def teardown(self):
        del self.empty_func
        del self.buf

    def test_generate_header_empty_func(self):
        pname = "DP"
        fc_wrap.GenCHeader(pname).generate([self.empty_func], self.buf)
        header_file = '''
#include "config.h"
fwrap_default_int empty_func_c();
'''.splitlines()
        eq_(header_file, self.buf.getvalue().splitlines())

    def test_generate_pxd_empty_func(self):
        pname = "DP"
        fc_wrap.GenPxd(pname).generate([self.empty_func], self.buf)
        pxd_file = '''
cdef extern from "config.h":
    ctypedef int fwrap_default_int

cdef extern:
    fwrap_default_int empty_func_c()
'''.splitlines()
        eq_(pxd_file, self.buf.getvalue().splitlines())

def _test_gen_fortran_one_arg_func():
    pname = "FB"
    one_arg = pyf.Function(name='one_arg',
                           args=[pyf.Argument(name='a',
                                      dtype=pyf.Dtype(type='integer', ktp='fwrap_default_int'),
                                      intent="in")],
                           return_type=Dtype(type='integer', ktp='fwrap_default_int'))
    buf = CodeBuffer()
    fc_wrap.GenFortran(pname).generate([one_arg], buf)
    fort_file = '''
function fw_one_arg(a) bind(c, name="one_arg_c")
    use config
    implicit none
    integer(fwrap_default_int), intent(in) :: a
    integer(fwrap_default_int) :: fw_one_arg
    interface
        function one_arg(a)
            implicit none
            integer, intent(in) :: a
            integer :: empty_func
        end function one_arg
    end interface
    fw_one_arg = one_arg(a)
end function fw_one_arg
'''.splitlines()
    eq_(fort_file, buf.getvalue().splitlines())

def _test_gen_empty_func_wrapper():
    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_type=Dtype(type='integer', ktp='fwrap_default_int'))
    empty_func_wrapped = '''\
function fw_empty_func() bind(c, name="empty_func_c")
    use config
    implicit none
    integer(fwrap_default_int) :: fw_empty_func
    interface
        function empty_func()
            use config
            implicit none
            integer :: empty_func
        end function empty_func
    end interface
    fw_empty_func = empty_func()
end function fw_empty_func
'''
    buf = CodeBuffer()
    fc_wrap.FortranInterfaceGen(buf).generate_interface(empty_func)
    eq_(empty_func_wrapped, buf.getvalue(),
            msg='%s != %s' % (empty_func_wrapped, buf.getvalue()))

def test_procedure_argument_iface():
    passed_subr = pyf.Subroutine(name='passed_subr',
                       args=[pyf.Argument(name='arg1',
                                  dtype=pyf.Dtype(type='integer', ktp='fwrap_default_int'),
                                  intent='inout')])

    proc_arg_func = pyf.Function(name='proc_arg_func',
                         args=[passed_subr],
                         return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))

    proc_arg_iface = '''\
interface
    function proc_arg_func(passed_subr)
        use config
        implicit none
        interface
            subroutine passed_subr(arg1)
                use config
                implicit none
                integer(fwrap_default_int), intent(inout) :: arg1
            end subroutine passed_subr
        end interface
        integer(fwrap_default_int) :: proc_arg_func
    end function proc_arg_func
end interface
'''
    buf = CodeBuffer()
    fc_wrap.FortranInterfaceGen(buf).generate_interface(proc_arg_func)
    eq_(proc_arg_iface, buf.getvalue(), msg='%s != %s' % (proc_arg_iface, buf.getvalue()))

def test_gen_iface():

    def gen_iface_gen(ast, istr):
        buf = CodeBuffer()
        fc_wrap.FortranInterfaceGen(buf).generate_interface(ast)
        eq_(istr, buf.getvalue(), msg='%s != %s' % (istr, buf.getvalue()))


    many_arg_subr = pyf.Subroutine(name='many_arg_subr',
                         args=[pyf.Argument(name='arg1',
                                    dtype=pyf.Dtype(type='complex', ktp='fwrap_sik_10_20'),
                                    intent='in'),
                               pyf.Argument(name='arg2',
                                    dtype=pyf.Dtype(type='real', ktp='fwrap_double_precision'),
                                    intent='inout'),
                               pyf.Argument(name='arg3',
                                    dtype=pyf.Dtype(type='integer', ktp='fwrap_int_x_8'),
                                    intent='out')])
    many_arg_subr_iface = '''\
interface
    subroutine many_arg_subr(arg1, arg2, arg3)
        use config
        implicit none
        complex(fwrap_sik_10_20), intent(in) :: arg1
        real(fwrap_double_precision), intent(inout) :: arg2
        integer(fwrap_int_x_8), intent(out) :: arg3
    end subroutine many_arg_subr
end interface
'''

    one_arg_func = pyf.Function(name='one_arg_func',
                        args=[pyf.Argument(name='arg1',
                                  dtype=pyf.Dtype(type='real', ktp='fwrap_default_real'),
                                  intent='inout')],
                        return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
    one_arg_func_iface = '''\
interface
    function one_arg_func(arg1)
        use config
        implicit none
        real(fwrap_default_real), intent(inout) :: arg1
        integer(fwrap_default_int) :: one_arg_func
    end function one_arg_func
end interface
'''

    empty_func = pyf.Function(name='empty_func',
                      args=(),
                      return_type=pyf.Dtype(type='integer', ktp='fwrap_default_int'))
    empty_func_iface = '''\
interface
    function empty_func()
        use config
        implicit none
        integer(fwrap_default_int) :: empty_func
    end function empty_func
end interface
'''
    data = [(many_arg_subr, many_arg_subr_iface),
            (one_arg_func, one_arg_func_iface),
            (empty_func, empty_func_iface)]

    for ast, iface in data:
        yield gen_iface_gen, ast, iface