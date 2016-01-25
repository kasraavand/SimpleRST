import ast
import re
from operator import itemgetter
from os import path
from tempfile import NamedTemporaryFile
import shutil

class Parser(object):
	def __init__(self, *args, **kwargs):
		self.file_name = kwargs['file_name']
		self.file_contents = self.source_reader()
		self.module = self.create_parser_obj() 
		self.param_format = """   :param {name}: {describe}\n   :type {name}: {types}"""

	def source_reader(self):
		with open(self.file_name) as fd:
		    return fd.read()
	
	def create_parser_obj(self):
		return ast.parse(self.file_contents)

	def extract_info(self):
		for node in self.module.body: 
			if isinstance(node, ast.ClassDef):
				yield {
					"name": node.name,
					"lineno": node.lineno,
					"docstring": ast.get_docstring(node),
					"type": 'class',
					}
				for sub_node in node.body:
					if isinstance(sub_node, ast.FunctionDef):
						yield {
							"name": sub_node.name,
							"lineno": sub_node.lineno,
							"docstring": ast.get_docstring(sub_node),
							"type": 'attribute',
							"args": [arg.id for arg in sub_node.args.args],
							"header": ''
							}

			elif isinstance(node, ast.FunctionDef):
				yield {
					"name": node.name,
					"lineno": node.lineno,
					"docstring": ast.get_docstring(node),
					"type": 'function',
					"args": [arg.id for arg in node.args.args],
					}

	def parse_doc(self):
		objects_info = self.extract_info()
		regex = re.compile(r'^\s*([^:]*)\(([^)]*)\):(.*)$',re.DOTALL)
		for parsed_docstring in objects_info:
			doc = parsed_docstring.pop('docstring')
			parsed_docstring["arguments"] = []
			parsed_docstring["explain"] = ''
			if doc:
				doc_length = doc.count('\n')
				parsed_docstring["doc_length"] = doc_length
				doc_lines = doc.split('\n')
				indices = [i for i, line in enumerate(doc_lines) if regex.match(line)]
				
				if not indices:
					indices = [0]
				elif not indices[0] == 0:
					indices = [0]+indices

				parts_ = ['\n'.join(doc_lines[i:j]) for i, j in zip(indices, indices[1:]+[None])]
				for part in parts_:
					match_obj = regex.match(part)
					if match_obj:
						name, types, describe = match_obj.group(1, 2, 3)
						parsed_docstring["arguments"].append(
							{'name': name,'types': types,'describe': describe}
							)
					else:
						parsed_docstring["explain"] += '\n'+part

				yield doc_lines, parsed_docstring
			else:
				parsed_docstring['explain'] = ''
				if parsed_docstring['type'] in {'function', 'attribute'}:
					parsed_docstring['arguments'] = [
					{'name': i,
					 'types': '',
					 'describe': ''} for i in parsed_docstring['args']]
				else:
					parsed_docstring['arguments'] =[{'name': '','types': '','describe': ''}]
				parsed_docstring['doc_length'] = 0
				yield '', parsed_docstring
				

	def create_rst(self):
		parsed_docstring = self.parse_doc()
		for doc_lines, doc in parsed_docstring:
			name, lineno, type_, explain, arguments, doc_length= itemgetter(
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
					'name': name ,
					'lineno': lineno,
					'type': type_,
					'explain': explain,
					'params': params,
					'file_name': self.file_name,
					'return':'UNKNOWN',
					'note': '',
					'example': '',
					'todo':''
					})
			elif type_ == 'class':
				with open('temp_class.rst') as fi:
					EMPTY_RST = fi.read()
				FULL_RST = EMPTY_RST.format(**{
					'name': name ,
					'lineno': lineno,
					'type': type_,
					'explain':explain,
					'params': params,
					'args':'',
					'file_name': self.file_name,
					'return':'UNKNOWN',
					'note': '',
					'example': '',
					'todo': ''
					})
			elif type_ == 'attribute':
				with open('attribute.rst') as fi:
					EMPTY_RST = fi.read()
				FULL_RST = EMPTY_RST.format(**{
					'name': name ,
					'lineno': lineno,
					'type': type_,
					'explain':explain,
					'params': params,
					'args':'',
					'file_name': self.file_name,
					'return':'UNKNOWN',
					'note': '',
					'example': '',
					'todo': ''
					})
			yield lineno+1, FULL_RST, doc_length, doc_lines

	def replacer(self, flag=False, initial=False):
		tempfile = NamedTemporaryFile(delete=False)
		with open(self.file_name.split('.')[0]+'.rst', 'w') as rst,open(self.file_name) as py:
			rst_iterator = self.create_rst()
			lineno, FULL_RST, doc_length, doc_lines = next(rst_iterator)
			pre_lineno = lineno
			rst.write(FULL_RST)
			for index,line in enumerate(py,1):
				if index == lineno:
					if line.strip().endswith(':') and line.count('(') != line.count(')'):
						lineno+=1
						tempfile.write(line)
						continue
					else:
						if doc_length == 0:
							tempfile.write('\t"""\n'+FULL_RST+'\t"""\n')
							flag = True
						else :
							tempfile.write('\t"""\n'+FULL_RST+'\t"""\n')
							flag = False
						try:
							pre_doc_lines = doc_lines
							lineno, FULL_RST, doc_length, doc_lines = next(rst_iterator)
							rst.write(FULL_RST)
						except StopIteration:
							pass
						initial = True

				elif initial:
					if flag and line.strip() not in pre_doc_lines and line.strip() != '"""':
						tempfile.write(line)
						print line,'**',doc_lines
					else:
						if line.strip() != '"""':
							pass
						else:
							flag = True
				else:
 					tempfile.write(line)


				
			shutil.move(tempfile.name, self.file_name)



if __name__ == "__main__":
	Pars = Parser(file_name='the_relative_path')
	Pars.replacer()
