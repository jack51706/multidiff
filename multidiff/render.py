import binascii
import termcolor
import html

class Render():
	'''Configure the output encoding and coloring method of this rendering object'''
	def __init__(self, encode='hexdump', color='ansi'):
		if   color == 'ansi':
			self.highligther = ansi_colored
		elif color == 'html':
			self.highligther = html_colored

		if   encode == 'hexdump':
			self.encoder = HexdumpEncoder
		elif encode == 'hex':
			self.encoder = HexEncoder
		elif encode == 'utf8':
			self.encoder = Utf8Encoder
			
	'''Render the diff in the given model into a UTF-8 String'''
	def render(self, model, diff):
		result = self.encoder(self.highligther)
		obj = model.objects[diff.target]
		for op in diff.opcodes:
			data = obj.data[op[3]:op[4]]
			result.append(data, op[0])
		return result.final()

	'''Dump all diffs in a model. Mostly good for debugging'''
	def dumps(self, model):
		dump = ""
		for diff in model.diffs:
			dump += self.render(model, diff) + '\n'
		return dump

'''A string (utf8) encoder for the data'''
class Utf8Encoder():
	def __init__(self, highligther):
		self.highligther = highligther
		self.output = ''

	def append(self, data, color):
		self.output += self.highligther(str(data, 'utf8'), color)
	
	def final(self):
		return self.output

'''A hex encoder for the data'''
class HexEncoder():
	def __init__(self, highligther):
		self.highligther = highligther
		self.output = ''
	def append(self, data, color):
		data = str(binascii.hexlify(data),'utf8')
		self.output += self.highligther(data, color)
	
	def final(self):
		return self.output

'''A hexdump encoder for the data'''
class HexdumpEncoder():
	def __init__(self, highligther):
		self.highligther = highligther
		self.body = ''
		self.addr = 0
		self.rowlen = 0
		self.hexrow = ''
		self.skipspace = False
		self.asciirow = ''

	def append(self, data, color):
		if len(data) == 0:
			self._append(data, color)
		while len(data) > 0:
			if self.rowlen == 16:
				self._newrow()
			consumed = self._append(data[:16 - self.rowlen], color)
			data = data[consumed:]

	def _append(self, data, color):
		if len(data) == 0:
			#in the case of highlightig a deletion in a target or an
			#addition in the source, print a highlighted space and mark
			#it skippanble for the next append
			hexs = ' ' 
			self.skipspace = True
		else:
			self._add_hex_space()
			#encode to hex and add some spaces
			hexs = str(binascii.hexlify(data), 'utf8')
			hexs = ' '.join([hexs[i:i+2] for i in range(0, len(hexs), 2)])
			asciis = ''
			#make the ascii dump
			for byte in data:
				if 0x20 <= byte <= 0x7E:
					asciis += chr(byte)
				else:
					asciis += '.'
			self.asciirow += self.highligther(asciis, color)

		self.hexrow   += self.highligther(hexs, color)
		self.rowlen += len(data)
		return len(data)

	def _newrow(self):
		self._add_hex_space()
		if self.addr != 0:
			self.body += '\n'
		self.body += "{:06x}:{:s}|{:s}|".format(
			self.addr, self.hexrow, self.asciirow);
		self.addr += 16
		self.rowlen = 0
		self.hexrow = ''
		self.asciirow = ''

	def _add_hex_space(self):
		if self.skipspace:
			self.skipspace = False
		else:
			self.hexrow += ' '
		

	def final(self):
		self.hexrow += 3*(16 - self.rowlen) * ' '
		self.asciirow += (16 - self.rowlen) * ' '
		self._newrow()
		return self.body

def ansi_colored(string, op):
	if   op == 'equal':
		return string
	elif op == 'replace':
		color = 'blue'
	elif op == 'insert':
		color = 'green'
	elif op == 'delete':
		color = 'red'
	return termcolor.colored(string, 'white', 'on_{}'.format(color))
	#return termcolor.colored(string, color, None)

def html_colored(string, op):
	if   op == 'equal':
		return string
	return "<span class='" + op + "'>" + html.escape(string) + "</span>"
