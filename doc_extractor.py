
import argparse
import ast
import glob
from os import path as ospath, mkdir, walk
from itertools import chain


class Parser(object):

    def __init__(self, *args, **kwargs):
        self.input_path = kwargs['input_path']
        self.output_path = kwargs['output_path']
        self.projct_name = kwargs['projct_name']
        if not ospath.isdir(self.output_path):
            mkdir(self.output_path)

    def get_doc(self, module):
        for node in module.body:
            if isinstance(node, ast.ClassDef):
                yield ast.get_docstring(node)
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef):
                        yield ast.get_docstring(sub_node)

    def rst_creator(self):
        if self.input_path.endswith(".py"):
            with open(input_path) as f:
                self.generate_rst(f, input_path, True)
        else:
            for dirpath, dirnames, filenames in walk(input_path):
                for dirname in dirnames:
                    doc = chain.form_iterable(self.generate_rst(ospath.join(input_path, dirname)))
                    with open(dirname, 'w') as f:
                        f.write("\n".join(doc))

    def generate_rst(self, path):
        for name in glob.glob(path + "/**/*.py",
                              recursive=True):
            with open(name) as f:
                yield self.create_rst(f, name)

    def create_rst(self, inp, name, one_file=False):
        for doc in self.get_doc(ast.parse(inp.read())):
            if doc and not doc.strip().startswith("@"):
                yield doc

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Extract RST documentations from files.
        """)
    parser.add_argument("-i",
                        "-input",
                        help="The input directory.")
    parser.add_argument("-o",
                        "-output",
                        help="The output directory.")
    parser.add_argument("-p",
                        "-projct_name",
                        help="The name of base directory for project.")
    args = parser.parse_args()

    input_path, output_path, projct_name = args.i, args.o, args.p
    PS = Parser(input_path=input_path,
                output_path=output_path,
                projct_name=projct_name)
    PS.rst_creator()
