# ------------------------------------------------------------------------------
# Copyright (c) 2010, Kurt W. Smith
# All rights reserved. See LICENSE.txt.
# ------------------------------------------------------------------------------

#
#   Tree visitor and transform framework
#
# Ripped out of Cython and used for expression tree parsing.

import inspect
from Cython.Compiler.ExprNodes import ExprNode, NameNode
from Cython.Compiler.Nodes import DefNode, Node


class BasicVisitor(object):
    """A generic visitor base class which can be used for visiting any kind of object."""

    # Note: If needed, this can be replaced with a more efficient metaclass
    # approach, resolving the jump table at module load time rather than per visitor
    # instance.
    def __init__(self):
        self.dispatch_table = {}

    def visit(self, obj):
        cls = type(obj)
        try:
            handler_method = self.dispatch_table[cls]
        except KeyError:
            # print "Cache miss for class %s in visitor %s" % (
            #    cls.__name__, type(self).__name__)
            # Must resolve, try entire hierarchy
            pattern = "visit_%s"
            mro = inspect.getmro(cls)
            handler_method = None
            for mro_cls in mro:
                if hasattr(self, pattern % mro_cls.__name__):
                    handler_method = getattr(self, pattern % mro_cls.__name__)
                    break
            if handler_method is None:
                print(type(self), type(obj))
                if hasattr(self, 'access_path') and self.access_path:
                    print(self.access_path)
                    if self.access_path:
                        # print self.access_path[-1][0].pos
                        print(self.access_path[-1][0].__dict__)
                raise RuntimeError("Visitor does not accept object: %s of type %s" % (obj, type(obj)))
            # print "Caching " + cls.__name__
            self.dispatch_table[cls] = handler_method
        return handler_method(obj)


class TreeVisitor(BasicVisitor):
    """
    Base class for writing visitors for a Cython tree, contains utilities for
    recursing such trees using visitors. Each node is
    expected to have a child_attrs iterable containing the names of attributes
    containing child nodes or lists of child nodes. Lists are not considered
    part of the tree structure (i.e. contained nodes are considered direct
    children of the parent node).
    
    visit_children visits each of the children of a given node (see the visit_children
    documentation). When recursing the tree using visit_children, an attribute
    access_path is maintained which gives information about the current location
    in the tree as a stack of tuples: (parent_node, attrname, index), representing
    the node, attribute and optional list index that was taken in each step in the path to
    the current node.
    
    Example:
    
    >>> class SampleNode(object):
    ...     child_attrs = ["head", "body"]
    ...     def __init__(self, value, head=None, body=None):
    ...         self.value = value
    ...         self.head = head
    ...         self.body = body
    ...     def __repr__(self): return "SampleNode(%s)" % self.value
    ...
    >>> tree = SampleNode(0, SampleNode(1), [SampleNode(2), SampleNode(3)])
    >>> class MyVisitor(TreeVisitor):
    ...     def visit_SampleNode(self, node):
    ...         print "in", node.value, self.access_path
    ...         self.visitchildren(node)
    ...         print "out", node.value
    ...
    >>> MyVisitor().visit(tree)
    in 0 []
    in 1 [(SampleNode(0), 'head', None)]
    out 1
    in 2 [(SampleNode(0), 'body', 0)]
    out 2
    in 3 [(SampleNode(0), 'body', 1)]
    out 3
    out 0
    """

    def __init__(self):
        super(TreeVisitor, self).__init__()
        self.access_path = []

    def dump_node(self, node, indent=0):
        ignored = list(node.child_attrs) + ['child_attrs', 'pos',
                                            'gil_message', 'subexprs']
        values = []
        pos = node.pos
        if pos:
            source = pos[0]
            if source:
                import os.path
                source = os.path.basename(source.get_description())
            values.append('%s:%s:%s' % (source, pos[1], pos[2]))
        attribute_names = dir(node)
        attribute_names.sort()
        for attr in attribute_names:
            if attr in ignored:
                continue
            if attr.startswith('_') or attr.endswith('_'):
                continue
            try:
                value = getattr(node, attr)
            except AttributeError:
                continue
            if value is None or value == 0:
                continue
            elif isinstance(value, list):
                value = '[...]/%d' % len(value)
            elif not isinstance(value, (str, int, float)):
                continue
            else:
                value = repr(value)
            values.append('%s = %s' % (attr, value))
        return '%s(%s)' % (node.__class__.__name__,
                           ',\n    '.join(values))

    def _find_node_path(self, stacktrace):
        import os.path
        last_traceback = stacktrace
        nodes = []
        while hasattr(stacktrace, 'tb_frame'):
            frame = stacktrace.tb_frame
            node = frame.f_locals.get('self')
            if isinstance(node, Node):
                code = frame.f_code
                method_name = code.co_name
                pos = (os.path.basename(code.co_filename),
                       code.co_firstlineno)
                nodes.append((node, method_name, pos))
                last_traceback = stacktrace
            stacktrace = stacktrace.tb_next
        return last_traceback, nodes

    def visitchild(self, child, parent, attrname, idx):
        self.access_path.append((parent, attrname, idx))

        result = self.visit(child)

        # except Errors.CompileError:
        # raise
        # except Exception, e:
        # import sys
        # trace = ['']
        # for parent, attribute, index in self.access_path:
        # node = getattr(parent, attribute)
        # if index is None:
        # index = ''
        # else:
        # node = node[index]
        # index = u'[%d]' % index
        # trace.append(u'%s.%s%s = %s' % (
        # parent.__class__.__name__, attribute, index,
        # self.dump_node(node)))
        # stacktrace, called_nodes = self._find_node_path(sys.exc_info()[2])
        # last_node = child
        # for node, method_name, pos in called_nodes:
        # last_node = node
        # trace.append(u"File '%s', line %d, in %s: %s" % (
        # pos[0], pos[1], method_name, self.dump_node(node)))
        # raise Errors.CompilerCrash(
        # last_node.pos, self.__class__.__name__,
        # u'\n'.join(trace), e, stacktrace)
        # self.access_path.pop()
        return result

    def visitchildren(self, parent, attrs=None):
        """
        Visits the children of the given parent. If parent is None, returns
        immediately (returning None).
        
        The return value is a dictionary giving the results for each
        child (mapping the attribute name to either the return value
        or a list of return values (in the case of multiple children
        in an attribute)).
        """

        if parent is None:
            return None
        result = {}
        for attr in parent.child_attrs:
            if attrs is not None and attr not in attrs:
                continue
            child = getattr(parent, attr)
            if child is not None:
                if isinstance(child, list):
                    childretval = [self.visitchild(x, parent, attr, idx) for idx, x in enumerate(child)]
                else:
                    childretval = self.visitchild(child, parent, attr, None)
                    assert not isinstance(childretval, list), 'Cannot insert list here: %s in %r' % (attr, parent)
                result[attr] = childretval
        return result


class PrintTree(TreeVisitor):
    """Prints a representation of the tree to standard output.
    Subclass and override repr_of to provide more information
    about nodes. """

    def __init__(self):
        TreeVisitor.__init__(self)
        self._indent = ""

    def indent(self):
        self._indent += "  "

    def unindent(self):
        self._indent = self._indent[:-2]

    def __call__(self, tree, phase=None):
        print(("Parse tree dump at phase '%s'" % phase))
        self.visit(tree)
        return tree

    # Don't do anything about process_list, the defaults gives
    # nice-looking name[idx] nodes which will visually appear
    # under the parent-node, not displaying the list itself in
    # the hierarchy.
    def visit_Node(self, node):
        if len(self.access_path) == 0:
            name = "(root)"
        else:
            parent, attr, idx = self.access_path[-1]
            if idx is not None:
                name = "%s[%d]" % (attr, idx)
            else:
                name = attr
        print(("%s- %s: %s" % (self._indent, name, self.repr_of(node))))
        self.indent()
        self.visitchildren(node)
        self.unindent()
        return node

    def repr_of(self, node):
        if node is None:
            return "(none)"
        else:
            result = node.__class__.__name__
            if isinstance(node, NameNode):
                result += "(type=%s, name=\"%s\")" % (repr(node.type), node.name)
            elif isinstance(node, DefNode):
                result += "(name=\"%s\")" % node.name
            elif isinstance(node, ExprNode):
                t = node.type
                result += "(type=%s)" % repr(t)
            elif node.pos:
                pos = node.pos
                path = pos[0].get_description()
                if '/' in path:
                    path = path.split('/')[-1]
                if '\\' in path:
                    path = path.split('\\')[-1]
                result += "(pos=(%s:%s:%s))" % (path, pos[1], pos[2])

            return result
