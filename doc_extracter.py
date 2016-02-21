

import ast


class Parser(object):

    def __init__(self, *args, **kwargs):
        self.file_name = kwargs['file_name']
        self.file_contents = self.source_reader()
        self.module = self.create_parser_obj()

    def source_reader(self):
        with open(self.file_name) as fd:
            return fd.read()

    def create_parser_obj(self):
        return ast.parse(self.file_contents)

    def get_doc(self):
        for node in self.module.body:
            if isinstance(node, ast.ClassDef):
                yield ast.get_docstring(node)
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        yield ast.get_docstring(sub_node)

    def rst_creator(self):
        name = self.file_name.rsplit('/', 1)[-1].split('.')[0]
        with open('{}.rst'.format(name), 'w') as f:
            for doc in self.get_doc():
                if doc:
                    doc = unicode(doc,'unicode-escape').replace(u'”', '`').replace(u'“', '`')
                    f.write(doc + '\n')

if __name__ == '__main__':
    PS = Parser(file_name='')
    PS.rst_creator()
