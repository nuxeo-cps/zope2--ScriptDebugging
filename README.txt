FSPythonScript Support for pdb
------------------------------

This Product monkey patches Zope and to allow pdb and other pdb based 
debuggers (such as Wing IDE) to stop on breakpoints placed in script 
files stored on disk and to step into and through script file code.

The Monkeypatches are based on Zope 2.7.2 and CMF 1.4.2, and may not
work with other versions (but they probably will).

Unpatched Zope and derived code such as CMFCore and CMFFormController set
the co_filename attribute in the code objects produced from script files
to the string "Script (Python)", and strip meta data header comments from
the script file before compiling it, causing line number information in
the byte code to be incorrect. This prevents Wing's debugger (or any
other debugger) from determining where instructions in the code objects
come from, and thus makes it impossible to stop at breakpoints or step
through those files. This products fixes this. It does not create debugging
support for ZODB based Python scripts, but only for the file system based
FSPythonScripts.


This product is based on patches by Stephan Deibel (sdeibel@wingware.com),
and made into a product by Lennart Regebro.

The original patches can be found here:
http://collector.zope.org/CMF/194

For more information, please contact regebro@nuxeo.com, or support@wingide.com.

