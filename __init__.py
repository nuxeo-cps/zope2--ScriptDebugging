##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Python Scripts Debugging Support
$Id$'''
__version__='$Revision$'[11:-2]

import sys, marshal
from zLOG import LOG, ERROR

from Shared.DC.Scripts.Script import defaultBindings

from Products.PythonScripts.PythonScript import PythonScript, Python_magic, \
    Script_magic, _nonempty_line, _first_indent, _nice_bind_names

from AccessControl import ModuleSecurityInfo
ModuleSecurityInfo('pdb').declarePublic('set_trace')
    
# Add support for storing a path to the file.
def __init__(self, id, filepath=None):
    self.id = id
    if filepath:
        self._filepath = filepath
    self.ZBindings_edit(defaultBindings)
    self._makeFunction()

PythonScript.__init__ = __init__
        
# If filepath exists, it is used instead of the meta_type.
# If not, the meta type is used as before.
def _compile(self):
    
    fp = getattr(self, '_filepath', self.meta_type)
    bind_names = self.getBindingAssignments().getAssignedNamesInOrder()
    r = self._compiler(self._params, self._body or 'pass',
                        self.id, fp, globalize=bind_names)
    code = r[0]
    errors = r[1]
    self.warnings = tuple(r[2])
    if errors:
        self._code = None
        self._v_ft = self._v_f = None
        self._setFuncSignature((), (), 0)
        # Fix up syntax errors.
        filestring = '  File "<string>",'
        for i in range(len(errors)):
            line = errors[i]
            if line.startswith(filestring):
                errors[i] = line.replace(filestring, '  Script', 1)
        self.errors = errors
        return

    self._code = marshal.dumps(code)
    self.errors = ()
    f = self._newfun(code)
    fc = f.func_code
    self._setFuncSignature(f.func_defaults, fc.co_varnames,
                            fc.co_argcount)
    self.Python_magic = Python_magic
    self.Script_magic = Script_magic
    self._v_change = 0

PythonScript._compile = _compile

# The stripping of the header is moved from write() to the read() method.
def write(self, text):
    """ Change the Script by parsing a read()-style source text. """
    self._validateProxy()
    mdata = self._metadata_map()
    bindmap = self.getBindingAssignments().getAssignedNames()
    bup = 0

    st = 0
    try:
        while 1:
            # Find the next non-empty line
            m = _nonempty_line.search(text, st)
            if not m:
                # There were no non-empty body lines
                body = ''
                break
            line = m.group(0).strip()
            if line[:2] != '##':
                # We have found the first line of the body
                body = text
                break

            st = m.end(0)
            # Parse this header line
            if len(line) == 2 or line[2] == ' ' or '=' not in line:
                # Null header line
                continue
            k, v = line[2:].split('=', 1)
            k = k.strip().lower()
            v = v.strip()
            if not mdata.has_key(k):
                SyntaxError, 'Unrecognized header line "%s"' % line
            if v == mdata[k]:
                # Unchanged value
                continue

            # Set metadata value
            if k == 'title':
                self.title = v
            elif k == 'parameters':
                self._params = v
            elif k[:5] == 'bind ':
                bindmap[_nice_bind_names[k[5:]]] = v
                bup = 1

        body = body.rstrip()
        if body:
            body = body + '\n'
        if body != self._body:
            self._body = body
        if bup:
            self.ZBindings_edit(bindmap)
        else:
            self._makeFunction()
    except:
        LOG(self.meta_type, ERROR, 'write failed', error=sys.exc_info())
        raise

PythonScript.write = write

# The stripping of the header is moved from write() to the read() method.
def read(self):
    """ Generate a text representation of the Script source.

    Includes specially formatted comment lines for parameters,
    bindings, and the title.
    """
    # Construct metadata header lines, indented the same as the body.
    m = _first_indent.search(self._body)
    if m: prefix = m.group(0) + '##'
    else: prefix = '##'

    hlines = ['%s %s "%s"' % (prefix, self.meta_type, self.id)]
    mm = self._metadata_map().items()
    mm.sort()
    for kv in mm:
        hlines.append('%s=%s' % kv)
    if self.errors:
        hlines.append('')
        hlines.append(' Errors:')
        for line in self.errors:
            hlines.append('  ' + line)
    if self.warnings:
        hlines.append('')
        hlines.append(' Warnings:')
        for line in self.warnings:
            hlines.append('  ' + line)
    hlines.append('')

    # Strip old header from existing body before adding new one
    st = 0
    while 1:
        # Find the next non-empty line
        m = _nonempty_line.search(self._body, st)
        if not m:
            # There were no non-empty body lines
            body = ''
            break
        line = m.group(0).strip()
        st = m.end(0)
        if line[:2] != '##':
            # We have found the first line of the body
            body = self._body[m.start(0):]
            break
    body = body.rstrip()
    if body:
        body = body + '\n'

    return ('\n' + prefix).join(hlines) + '\n' + body

PythonScript.read = read

try:
    from Products.CMFCore.FSPythonScript import FSPythonScript
    from Products.CMFCore.DirectoryView import expandpath
except ImportError:
    pass
else:
    
    # Now includes the filepath
    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        obj = PythonScript(self.getId(), expandpath(self._filepath))
        obj.write(self.read())
        return obj

    FSPythonScript._createZODBClone = _createZODBClone

    # Now includes the file path
    def _write(self, text, compile):
        '''
        Parses the source, storing the body, params, title, bindings,
        and source in self.  If compile is set, compiles the
        function.
        '''
        ps = PythonScript(self.id, expandpath(self._filepath))
        ps.write(text)
        if compile:
            ps._makeFunction(1)
            self._v_f = f = ps._v_f
            if f is not None:
                self.func_code = f.func_code
                self.func_defaults = f.func_defaults
            else:
                # There were errors in the compile.
                # No signature.
                self.func_code = bad_func_code()
                self.func_defaults = None
        self._body = ps._body
        self._params = ps._params
        self.title = ps.title
        self._setupBindings(ps.getBindingAssignments().getAssignedNames())
        self._source = ps.read()  # Find out what the script sees.

    FSPythonScript._write =_write
