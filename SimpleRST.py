import ast
import re
from operator import itemgetter
from tempfile import NamedTemporaryFile
from collections import deque
from itertools import tee, izip_longest
import shutil


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
    def __init__(self, *args, **kwargs):
        """
        .. py:attribute:: __init__()

            Constructor of Parser objects

           :param file_name: The name of target file
           :type file_name: string
           :param file_contents: The content of input file
           :type file_contents: string
           :param param_format: A raw frame of parameter line in RST formatting
           :type param_format: string
           :param whitespace_regex: A regex for extracting the leading
            whitespace from code lines
           :type: regex object
           :rtype: None
        """
        self.file_name = kwargs['file_name']
        self.file_contents = ''.join(self.source_reader_filtered())  # self.source_reader()
        self.module = self.create_parser_obj()
        self.param_format = """   :param {name}: {describe}\n   :type {name}: {types}"""
        self.whitespace_regex = re.compile(r"^(\s*).*")

    def source_reader_filtered(self):
        """
        .. py:attribute:: source_reader_filtered()

            Read the content of input file by ignoring the escaped new line characters.
           :rtype: string

        """
        with open(self.file_name) as f:
            stack = deque()
            ne, f = tee(f)
            next(ne)
            for line, next_line in izip_longest(f, ne):
                line = line.rstrip()
                if line.endswith('\\'):
                    stack.append(line.strip('\\'))
                else:
                    yield ''.join(stack) + line + '\n'
                    stack.clear()

    def create_parser_obj(self):
        """
        .. py:attribute:: create_parser_obj()

           Pass the source file content to `ast.parser` function in order to
           create a parser object.

           :rtype: `ast.parser` object

        """
        return ast.parse(self.file_contents)

    def extract_info(self):
        """
        .. py:attribute:: extract_info()

           This function loop over parser object and extracts the informations
           (contains name, documentation, line number etc.) for function, class
           and attribute objects.

           :rtype: dict

        .. note::

        """
        for node in self.module.body:
            if isinstance(node, ast.ClassDef):
                yield {
                    "name": node.name,
                    "lineno": node.lineno - 1,
                    "docstring": ast.get_docstring(node),
                    "type": 'class'}
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        yield {
                            "name": sub_node.name,
                            "lineno": sub_node.lineno - 1,
                            "docstring": ast.get_docstring(sub_node),
                            "type": 'attribute',
                            "args": [arg.id for arg in sub_node.args.args if arg.id != 'self'],
                            "header": ''}
            elif isinstance(node, ast.FunctionDef):
                yield {
                    "name": node.name,
                    "lineno": node.lineno - 1,
                    "docstring": ast.get_docstring(node),
                    "type": 'function',
                    "args": [arg.id for arg in node.args.args]}


    def parse_doc(self):
        """
        .. py:attribute:: parse_doc()


           :param self:
           :type self:
           :rtype: UNKNOWN

        .. note::

        .. todo::
        """
        objects_info = self.extract_info()
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

    def create_rst(self):
        """
        .. py:attribute:: create_rst()


           :param self:
           :type self:
           :rtype: UNKNOWN

        .. note::

        .. todo::
        """
        parsed_docstring = self.parse_doc()
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
                    EMPTY_RST = fi.read()
                FULL_RST = EMPTY_RST.format(**{
                    'args': args,
                    'name': name,
                    'lineno': lineno,
                    'type': type_,
                    'explain': explain,
                    'params': params,
                    'file_name': self.file_name,
                    'return': 'UNKNOWN',
                    'note': '',
                    'example': '',
                    'todo': ''})
            elif type_ == 'class':
                with open('temp_class.rst') as fi:
                    EMPTY_RST = fi.read()
                FULL_RST = EMPTY_RST.format(**{
                    'name': name,
                    'lineno': lineno,
                    'type': type_,
                    'explain': explain,
                    'params': params,
                    'args': '',
                    'file_name': self.file_name,
                    'return': 'UNKNOWN',
                    'note': '',
                    'example': '',
                    'todo': ''})
            elif type_ == 'attribute':
                with open('attribute.rst') as fi:
                    EMPTY_RST = fi.read()
                FULL_RST = EMPTY_RST.format(**{
                    'name': name,
                    'lineno': lineno,
                    'type': type_,
                    'explain': explain,
                    'params': params,
                    'args': '',
                    'file_name': self.file_name,
                    'return': 'UNKNOWN',
                    'note': '',
                    'example': '',
                    'todo': ''})
            yield lineno + 1, FULL_RST, doc_length, doc_lines

    def replacer(self, doc_flag=False, initial=False, whitespace=None):
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
        tempfile = NamedTemporaryFile(delete=False)
        with open(self.file_name.split('.')[0] + '.rst', 'w') as rst:
            py = self.source_reader_filtered()
            rst_iterator = self.create_rst()
            lineno, FULL_RST, doc_length, doc_lines = next(rst_iterator)
            rst.write(FULL_RST)
            for index, line in enumerate(py, 1):
                # If we encounter a class, function or attribute header
                strip_line = line.strip()
                if index == lineno:
                    if not whitespace:
                        whitespace = self.whitespace_regex.search(line).group(1)
                    # If object header got finished in this line (existence of `:` at the end of line)
                    if strip_line.endswith(':'):
                        tempfile.write(line)
                        # Preparing the leading whitespace
                        if '\t' in whitespace:
                            whitespace += "\t"
                        else:
                            whitespace += "    "
                        # If the object hasn't any doc by itself we write the FULL_RST and make the
                        # doc_flag True in order to be use in next steps
                        if doc_length == 0:
                            tempfile.write(
                                ''.join([
                                    whitespace,
                                    '"""\n',
                                    '\n'.join([whitespace + l for l in FULL_RST.split('\n')]),
                                    '"""\n']))
                            doc_flag = True

                        else:
                            # If object has doc write the FULL_RST and make the doc_flag False
                            tempfile.write(
                                ''.join([
                                    whitespace,
                                    '"""\n',
                                    '\n'.join([whitespace + l for l in FULL_RST.split('\n')]),
                                    '"""\n']))
                            doc_flag = False

                        # clear the previous white space in order to be reconstruct for next objects.
                        whitespace = None
                        # making initial True means we have written the documentation
                        initial = True
                        try:
                            # Preserve the documentation and iterate over rst_iterator
                            pre_doc_lines = doc_lines
                            lineno, FULL_RST, doc_length, doc_lines = next(rst_iterator)
                            rst.write(FULL_RST)
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
                    stripp_line = line.strip()
                    # If doc_flag be True means that object hasn't doc so we can write the next lines incautious.
                    if doc_flag:
                        tempfile.write(line)
                        initial = False
                    # otherwise if the line is a whitespace we write it.
                    elif not stripp_line:
                        tempfile.write(line)
                    # Else if line in not in previous doc lines we we write it
                    elif stripp_line not in map(str.strip, pre_doc_lines + ['"""']):
                        tempfile.write(line)
                # If line is not a the header of an object and initial is not True we just write the line.
                else:
                    tempfile.write(line)
            # Replace the temporary file with target file.
            shutil.move(tempfile.name, self.file_name)


if __name__ == "__main__":
    Pars = Parser(file_name='')
    Pars.replacer()
