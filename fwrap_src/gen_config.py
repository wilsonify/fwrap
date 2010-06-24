from cPickle import dumps
from fwrap_src import pyf_iface
import constants

def read_type_spec(fname):
    from cPickle import loads
    fh = open(fname, 'rb')
    ds = loads(fh.read())
    fh.close()
    return [ConfigTypeParam(**d) for d in ds]

def write_f_mod(fname, ctps):
    f_out = open(fname, 'w')
    try:
        f_out.write('''
module fwrap_ktp_mod
    use iso_c_binding
    implicit none
''')
        for ctp in ctps:
            for line in ctp.gen_f_mod():
                f_out.write('    %s\n' % line)
        f_out.write('end module fwrap_ktp_mod\n')
    finally:
        f_out.close()

def write_header(fname, ctps):
    h_out = open(fname, 'w')
    try:
        h_out.write("#ifndef %s\n" % fname.upper().replace('.','_'))
        h_out.write("#define %s\n" % fname.upper().replace('.', '_'))
        for ctp in ctps:
            for line in ctp.gen_c_includes():
                h_out.write(line+'\n')
        for ctp in ctps:
            for line in ctp.gen_c_typedef():
                h_out.write(line+'\n')
        for ctp in ctps:
            for line in ctp.gen_c_extra():
                h_out.write(line+'\n')

        h_out.write("#endif")
    finally:
        h_out.close()

def write_pxd(fname, h_name, ctps):
    pxd_out = open(fname, 'w')
    try:
        for ctp in ctps:
            for line in ctp.gen_pxd_intern_typedef():
                pxd_out.write(line+'\n')
        pxd_out.write('cdef extern from "%s":\n' % h_name)
        for ctp in ctps:
            for line in ctp.gen_pxd_extern_typedef():
                pxd_out.write('    '+line+'\n')
        for ctp in ctps:
            for line in ctp.gen_pxd_extern_extra():
                pxd_out.write('    '+line+'\n')
    finally:
        pxd_out.close()

def generate_type_specs(ast, buf):
    ctps = extract_ctps(ast)
    _generate_type_specs(ctps, buf)

def _generate_type_specs(ctps, buf):
    out_lst = []
    for ctp in ctps:
        out_lst.append(dict(basetype=ctp.basetype,
                            odecl=ctp.odecl,
                            fwrap_name=ctp.fwrap_name,
                            lang=ctp.lang))
    buf.write(dumps(out_lst))

def extract_ctps(ast):
    dtypes = set()
    for proc in ast:
        dtypes.update(proc.all_dtypes())
    dtypes = list(dtypes)
    return ctps_from_dtypes(dtypes)

def ctps_from_dtypes(dtypes):
    ret = []
    for dtype in dtypes:
        if dtype.odecl is None:
            continue
        ret.append(ConfigTypeParam(basetype=dtype.type,
                       fwrap_name=dtype.fw_ktp,
                       odecl=dtype.odecl,
                       lang=dtype.lang))
    return ret

def ConfigTypeParam(basetype, odecl, fwrap_name, lang='fortran'):
    if lang == 'c':
        return _CConfigTypeParam(basetype, odecl, fwrap_name)
    elif lang == 'fortran':
        if basetype == 'complex':
            return _CmplxTypeParam(basetype, odecl, fwrap_name)
        else:
            return _ConfigTypeParam(basetype, odecl, fwrap_name)
    else:
        raise ValueError("unknown language '%s' not one of 'c' or 'fortran'" % lang)

class _ConfigTypeParam(object):

    lang = 'fortran'

    def __init__(self, basetype, odecl, fwrap_name):
        self.basetype = basetype
        self.odecl = odecl
        self.fwrap_name = fwrap_name
        self.fc_type = None

    def __eq__(self, other):
        return self.basetype == other.basetype and \
                self.odecl == other.odecl and \
                self.fwrap_name == other.fwrap_name

    def cy_name(self):
        return self.fwrap_name

    def check_init(self):
        if self.fc_type is None:
            raise RuntimeError("fc_type is None, unable to "
                               "generate fortran type information.")

    def gen_f_mod(self):
        self.check_init()
        return ['integer, parameter :: %s = %s' % (self.fwrap_name, self.fc_type)]

    def gen_c_extra(self):
        return []

    def gen_c_includes(self):
        return []

    def gen_c_typedef(self):
        self.check_init()
        return ['typedef %s %s;' % (f2c[self.fc_type], self.fwrap_name)]

    def gen_pxd_extern_extra(self):
        return []

    def gen_pxd_extern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' % (f2c[self.fc_type], self.fwrap_name)]

    def gen_pxd_intern_typedef(self):
        return []

class _CmplxTypeParam(_ConfigTypeParam):

    _c2r_map = {'c_float_complex' : 'c_float',
               'c_double_complex' : 'c_double',
               'c_long_double_complex' : 'c_long_double'
               }

    _c2cy_map = {'c_float_complex' : 'float complex',
                 'c_double_complex' : 'double complex',
                 'c_long_double_complex' : 'long double complex'
                }
    
    def gen_c_includes(self):
        return ['#include <complex.h>']

    def gen_c_extra(self):
        self.check_init()
        return ("#define %(ktp)s_creal(x) (creal(x))\n"
                "#define %(ktp)s_cimag(x) (cimag(x))\n"
                "#define %(ktp)s_from_parts(r, i, x)"
                " (x = ((r) + _Complex_I * (i)))" % {'ktp' : self.fwrap_name}).splitlines()

    def gen_pxd_extern_extra(self):
        ctype = f2c[self._c2r_map[self.fc_type]]
        fktp = self.fwrap_name
        cyktp = self.cy_name()
        d = {'fktp' : fktp,
             'cyktp' : cyktp,
             'ctype' : ctype}
        code = ('%(ctype)s %(fktp)s_creal(%(fktp)s fdc)\n'
                '%(ctype)s %(fktp)s_cimag(%(fktp)s fdc)\n'
                'void %(fktp)s_from_parts(%(ctype)s r, %(ctype)s i, %(fktp)s fc)\n' % d)
        return code.splitlines()

    def gen_pxd_extern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' % (f2c[self._c2r_map[self.fc_type]], self.fwrap_name)]

    def gen_pxd_intern_typedef(self):
        self.check_init()
        return ['ctypedef %s %s' % (self._c2cy_map[self.fc_type], self.cy_name())]

    def cy_name(self):
        return "cy_%s" % self.fwrap_name


class _CConfigTypeParam(_ConfigTypeParam):

    lang = 'c'

f2c = {
    'c_int'             : 'int',
    'c_short'           : 'short int',
    'c_long'            : 'long int',
    'c_long_long'       : 'long long int',
    'c_signed_char'     : 'signed char',
    'c_size_t'          : 'size_t',
    'c_int8_t'          : 'int8_t',
    'c_int16_t'         : 'int16_t',
    'c_int32_t'         : 'int32_t',
    'c_int64_t'         : 'int64_t',
    'c_int_least8_t'    : 'int_least8_t',
    'c_int_least16_t'   : 'int_least16_t',
    'c_int_least32_t'   : 'int_least32_t',
    'c_int_least64_t'   : 'int_least64_t',
    'c_int_fast8_t'     : 'int_fast8_t',
    'c_int_fast16_t'    : 'int_fast16_t',
    'c_int_fast32_t'    : 'int_fast32_t',
    'c_int_fast64_t'    : 'int_fast64_t',
    'c_intmax_t'        : 'intmax_t',
    'c_intptr_t'        : 'intptr_t',
    'c_float'           : 'float',
    'c_double'          : 'double',
    'c_long_double'     : 'long double',
    'c_float_complex'   : 'float _Complex',
    'c_double_complex'  : 'double _Complex',
    'c_long_double_complex' : 'long double _Complex',
    'c_bool'            : '_Bool',
    'c_char'            : 'char',
    }

c2f = dict([(y,x) for (x,y) in f2c.items()])

type_dict = {
        'integer' : ('c_signed_char', 'c_short', 'c_int',
                  'c_long', 'c_long_long'),
        'real' : ('c_float', 'c_double', 'c_long_double'),
        'complex' : ('c_float_complex', 'c_double_complex', 'c_long_double_complex'),
        'character' : ('c_char',),
        }
type_dict['logical'] = type_dict['integer']
