import ast
import re
from operator import itemgetter, attrgetter
from tempfile import NamedTemporaryFile
from collections import deque, Iterable
from itertools import tee, izip_longest, dropwhile, chain
import shutil
import argparse
import fnmatch
import os


SIGNATURE = """Documentation created using SimpleRST. No kind of right reserved. It's all depends on you.
               Source: https://github.com/Kasramvd/SimpleRST\n"""


class Parser:
    """
    ==============

    ``Parser``
    ----------

    .. py:class:: Parser()

      This class aims to read the source of input file and then create_rst
      a parser object in order to extract the necessary information from source
      file. And then after parsing the existing documentations create the new
      documentation in form of RST formatting.

    """
    def __init__(self):
        """
        .. py:attribute:: __init__()

            Constructor of Parser objects
           :rtype: None
        """
        self.file_name = None
        self.next_iter = self.parser_iter = self.main_iter = self.file_contents = None

    def pars(self):
        module = self.create_parser_obj(self.file_contents)
        self.replacer(module)

    def create_refined_fileobj(self):
        f = open(self.file_name)
        refined_iter = dropwhile(lambda x: not x.strip(), f)
        self.next_iter, self.parser_iter, self.main_iter, self.file_contents = tee(refined_iter, 4)
        self.file_contents = ''.join(self.file_contents)
        return (self.next_iter,
                self.parser_iter,
                self.main_iter,
                self.file_contents)

    def source_reader_filtered(self):
        """
        .. py:attribute:: source_reader_filtered()

            Read the content of input file by ignoring the escaped new line characters.
           :rtype: string

        """
        stack = deque()
        next(self.next_iter)
        for line, next_line in izip_longest(self.parser_iter, self.next_iter):
            line = line.rstrip()
            if line.endswith('\\'):
                stack.append(line.strip('\\'))
            else:
                yield ''.join(stack) + line + '\n'
                stack.clear()

    def create_parser_obj(self, file_contents):
        """
        .. py:attribute:: create_parser_obj()

           Pass the source file content to `ast.parser` function in order to
           create a parser object.

           :rtype: `ast.parser` object

        """
        return ast.parse(file_contents)

    def extract_info(self, module):
        """
        .. py:attribute:: extract_info()

           This function loop over parser object and extracts the informations
           (contains name, documentation, line number etc.) for function, class
           and attribute objects.

           :rtype: dict

        .. note::

        """
        def extracter(root_nod):
            for node in root_nod.body:
                if isinstance(node, ast.ClassDef):
                    yield {
                        "name": node.name,
                        "lineno": node.lineno - 1,
                        "docstring": ast.get_docstring(node),
                        "type": 'class'}
                    for sub_node in node.body:
                        args_ = []
                        if isinstance(sub_node, ast.FunctionDef):
                            for arg in sub_node.args.args:
                                    try:
                                        args_.append(arg.id)
                                    except AttributeError:
                                        args_.extend([item.id for item in arg.elts if item.id != 'self'])

                            yield {
                                "name": sub_node.name,
                                "lineno": sub_node.lineno - 1,
                                "docstring": ast.get_docstring(sub_node),
                                "type": 'attribute',
                                "args": args_,
                                "header": ''}
                            for n in extracter(sub_node):
                                yield n
                elif isinstance(node, ast.FunctionDef):
                    args_ = []
                    for arg in node.args.args:
                        try:
                            args_.append(arg.id)
                        except AttributeError:
                            args_.extend([item.id for item in arg])
                    yield {
                        "name": node.name,
                        "lineno": node.lineno - 1,
                        "docstring": ast.get_docstring(node),
                        "type": 'function',
                        "args": args_}
                    for n in extracter(node):
                        yield n
        return extracter(module)


    def parse_doc(self, module):
        """
        .. py:attribute:: parse_doc()


           :param self:
           :type self:
           :rtype: UNKNOWN

        .. note::

        .. todo::
        """
        objects_info = self.extract_info(module)
        regex = re.compile(r'^\s*([^:]*)\(([^)]*)\):(.*)$', re.DOTALL)
        for parsed_docstring in objects_info:
            doc = parsed_docstring.pop('docstring')
            parsed_docstring["arguments"] = []
            parsed_docstring["explain"] = ''
            if doc:
                doc_lines = doc.split('\n')
                doc_length = len(doc_lines)
                parsed_docstring["doc_length"] = doc_length
                indices = [i for i, line in enumerate(doc_lines) if regex.match(line)]
                if not indices:
                    indices = [0]
                elif not indices[0] == 0:
                    indices = [0] + indices
                parts_ = ['\n'.join(doc_lines[i:j]) for i, j in zip(indices, indices[1:] + [None])]
                for part in parts_:
                    match_obj = regex.match(part)
                    if match_obj:
                        name, types, describe = match_obj.group(1, 2, 3)
                        parsed_docstring["arguments"].append(
                            {'name': name, 'types': types, 'describe': describe})
                    else:
                        parsed_docstring["explain"] += '\n' + part
                yield doc_lines, parsed_docstring
            else:
                parsed_docstring['explain'] = ''
                if parsed_docstring['type'] in {'function', 'attribute'}:
                    parsed_docstring['arguments'] = [{'name': i,
                                                      'types': '',
                                                      'describe': ''} for i in parsed_docstring['args']]
                else:
                    parsed_docstring['arguments'] = [{'name': '', 'types': '', 'describe': ''}]
                parsed_docstring['doc_length'] = 0
                yield [], parsed_docstring

    def create_rst(self, module):
        """
        .. py:attribute:: create_rst()


           :param self:
           :type self:
           :rtype: UNKNOWN

        .. note::

        .. todo::
        """
        parsed_docstring = self.parse_doc(module)
        for doc_lines, doc in parsed_docstring:
            name, lineno, type_, explain, arguments, doc_length = itemgetter(
                'name',
                'lineno',
                'type',
                'explain',
                'arguments',
                'doc_length')(doc)
            params = '\n'.join([self.param_format.format(**i) for i in arguments])
            if type_ == 'function':
                args = doc['args']
                with open('temp_function.rst') as fi:
                    empty_rst = fi.read()
                full_rst = empty_rst.format(**{
                    'args': args,
                    'name': name,
                    'lineno': lineno,
                    'type': type_,
                    'explain': explain,
                    'params': params,
                    'self.file_name': self.file_name,
                    'return': 'UNKNOWN',
                    'note': '',
                    'example': '',
                    'todo': ''})
            elif type_ == 'class':
                with open('temp_class.rst') as fi:
                    empty_rst = fi.read()
                full_rst = empty_rst.format(**{
                    'name': name,
                    'lineno': lineno,
                    'type': type_,
                    'explain': explain,
                    'params': params,
                    'args': '',
                    'self.file_name': self.file_name,
                    'return': 'UNKNOWN',
                    'note': '',
                    'example': '',
                    'todo': ''})
            elif type_ == 'attribute':
                with open('attribute.rst') as fi:
                    empty_rst = fi.read()
                full_rst = empty_rst.format(**{
                    'name': name,
                    'lineno': lineno,
                    'type': type_,
                    'explain': explain,
                    'params': params,
                    'args': '',
                    'self.file_name': self.file_name,
                    'return': 'UNKNOWN',
                    'note': '',
                    'example': '',
                    'todo': ''})
            yield lineno + 1, full_rst, doc_length, doc_lines

    def replacer(self, module, doc_flag=False, initial=False, whitespace=None):
        """
        .. py:attribute:: replacer()
            Replace the existing document (if it exist) or adding new document (if it hasn't doc)

           :param doc_flag: A boolean value for controlling the different states
           :type doc_flag: boolean
           :param initial: A boolean value for controlling the different states
           :type initial: boolean
           :rtype: None

        .. note::

        .. todo::
        """
        offset, module_doc, refined_iter = self.extract_module_doc()
        module_doc = self.module_doc_to_rst(module_doc)
        tempfile = NamedTemporaryFile(delete=False)
        tempfile.write(module_doc)
        rst_iterator = self.create_rst(module)
        lineno, full_rst, doc_length, doc_lines = next(rst_iterator)
        for index, line in enumerate(refined_iter, 1 + offset):
            # If we encounter a class, function or attribute header
            strip_line = line.strip()
            new_strip = strip_line.replace('"""', '')
            if new_strip:
                strip_line = new_strip
            if index == lineno:
                # refuse of matching he decorators.
                if strip_line.startswith('@'):
                    tempfile.write(line)
                    lineno += 1
                    continue
                if not whitespace:
                    whitespace = self.whitespace_regex.search(line).group(1)
                # If object header got finished in this line (existence of `:` at the end of line)
                if self.check_header(strip_line):
                    tempfile.write(line)
                    # Preparing the leading whitespace
                    if '\t' in whitespace:
                        whitespace += "\t"
                    else:
                        whitespace += "    "
                    # If the object hasn't any doc by itself we write the full_rst and make the
                    # doc_flag True in order to be use in next steps
                    if doc_length == 0:
                        tempfile.write(
                            ''.join([
                                whitespace,
                                '"""\n',
                                '\n'.join([whitespace + l.rstrip() if l.strip() else l for l in full_rst.split('\n')]),
                                whitespace,
                                '"""\n']))
                        doc_flag = True

                    else:
                        # If object has doc write the full_rst and make the doc_flag False
                        tempfile.write(
                            ''.join([
                                whitespace,
                                '"""\n',
                                '\n'.join([whitespace + l.rstrip() if l.strip() else l for l in full_rst.split('\n')]),
                                whitespace,
                                '"""\n']))
                        doc_flag = False

                    # clear the previous white space in order to be reconstruct for next objects.
                    whitespace = None
                    # making initial True means we have written the documentation
                    initial = True
                    try:
                        # Preserve the documentation and iterate over rst_iterator
                        pre_doc_lines = doc_lines
                        lineno, full_rst, doc_length, doc_lines = next(rst_iterator)
                    except StopIteration:
                        pass
                elif line.count('(') != line.count(')'):
                        # If we encounter a line and the line doesn't end with `:` means that header
                        # has been too long and has been divided to multiple parts.
                        tempfile.write(line)
                        lineno += 1
                else:
                    tempfile.write(line)

            # If the index != lineno and initial be True means that we have written the doc and still
            # we are in object body.
            elif initial:
                # If doc_flag be True means that object hasn't doc so we can write the next lines incautious.
                if doc_flag:
                    tempfile.write(line)
                    initial = False
                # otherwise if the line is a whitespace we write it.
                elif not strip_line:
                    tempfile.write(line)
                # Else if line in not in previous doc lines we we write it
                elif strip_line not in map(str.strip, pre_doc_lines + ['"""']):
                    tempfile.write(line)
            # If line is not a the header of an object and initial is not True we just write the line.
            else:
                tempfile.write(line)
            # Replace the temporary file with target file.
        shutil.move(tempfile.name, self.file_name)

    def check_header(self, line):
        if '#' in line:
            line = line.split('#')[0].strip()
            return line.endswith(':')
        return line.endswith(':')

    def extract_module_doc(self):
        shebang_lines = []
        doc_lines = []
        counter = 0
        for line in self.main_iter:
            strip_line = line.strip()
            if strip_line.startswith('#'):
                shebang_lines.append(line)
            elif strip_line.startswith('"""'):
                counter += 1
            elif counter % 2 == 0:
                return (len(doc_lines) + counter,
                        doc_lines,
                        chain(shebang_lines + [line], self.main_iter))
            else:
                doc_lines.append(line)

    def module_doc_to_rst(self, module_doc):
        module_doc = ''.join(module_doc).replace('"""', '')
        with open('module.rst') as fi:
            empty_rst = fi.read()
        full_rst = empty_rst.format(**{
            'file_name': self.file_name,
            'explanation': module_doc,
            'signature': SIGNATURE})
        return '"""\n' + full_rst + '"""\n\n'


class Manager(Parser):
    def __init__(self, *args, **kwargs):
        """
        .. py:attribute:: __init__()

           :param param_format: A raw frame of parameter line in RST formatting
           :type param_format: string
           :param whitespace_regex: A regex for extracting the leading
            whitespace from code lines
           :type: regex object

           :rtype: UNKNOWN

        .. note::

        .. todo::
        """
        # call the parent's constructor
        Parser().__init__()
        # get arguments
        self.args = kwargs['args']
        self.directory_path, self.file_name = self.get_args()
        self.whitespace_regex = re.compile(r"^(\s*).*")
        self.param_format = """   :param {name}: {describe}\n   :type {name}: {types}"""

    def get_args(self):
        return attrgetter('d', 'f')(self.args)

    @property
    def _file_name(self):
        return self.file_name

    @_file_name.setter
    def _file_name(self):
        self.file_name = self.file_name

    def run(self):
        """
        .. py:attribute:: run()

            Parse the input arguments and call the `pars()` function on file names
            based on the input arguments.
           :rtype: None

        .. note::

        .. todo::
        """
        if self.file_name:
            self.create_refined_fileobj()
            self.pars()
            print 'File " {} " gets documented'.format(os.path.basename(self.file_name))
        elif self.directory_path:
            for path, dirs, files in os.walk(self.directory_path):
                for file_name in fnmatch.filter(files, '*.py'):
                    self.file_name = '{}/{}'.format(path, file_name)
                    try:
                        self.create_refined_fileobj()
                        self.pars()
                    except (StopIteration, TypeError, IndentationError, SyntaxError) as e:
                        print "*** File {} gets escaped. ***\n*** {} ***".format(self.file_name, e)
                    else:
                        print 'File " {} " gets documented'.format(self.file_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Create RST doc for functions and classes from current doc and
        for no documented ones. In addition SimpleRST lets you create new document based
        on a manual pattern.
        """)
    parser.add_argument("-d",
                        "-directory",
                        help="Apply the code on all the files and sub-directories within given path")
    parser.add_argument("-f",
                        "-file",
                        help="Apply the code on given file name")
    args = parser.parse_args()
    manage = Manager(args=args)
    manage.run()
