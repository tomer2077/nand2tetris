import sys
import os

class Parser:
	'''Opens the input file/stream
	and gets ready to parse it'''
	def __init__(self, inputfile):
		self.commands = list(filter(lambda x : len(x) and x[0] != '/', (line.rstrip() for line in inputfile)))
		self.index = 0
		self.currentCommand = None
		self.commandTypes = {
			'push':		'C_PUSH',
			'pop':		'C_POP',
			'label':	'C_LABEL',
			'goto':		'C_GOTO',
			'if-goto':	'C_IF',
			'function':	'C_FUNCTION',
			'return':	'C_RETURN',
			'call':		'C_CALL'
		}
		self.commandTypes.update(dict.fromkeys(
		  ['sub', 'add', 'lt', 'gt', 'eq', 'neg', 'or', 'not', 'and'], 'C_ARITHMETIC'))
	
	# are there more commands in the input?
	def hasMoreCommands(self):
		if self.index < len(self.commands):
			return True
		else:
			return False

	# Only called if hasMoreCommands is true.
	# Reads next instruction from input and
	# makes it the current command
	def advance(self):
		# self.lastCommand = self.currentCommand
		# self.lastCommandType = self.commandType()
		self.currentCommand = self.commands[self.index].split()
		self.index += 1

	# Returns a constant representing the type
	# of the current command. C_ARITHMETIC
	# is returned for all arithmetic/logical commands
	def commandType(self):
		# print(self.currentCommand[0])
		return self.commandTypes[self.currentCommand[0]]

	# Returns the first argument of the current command
	# For C_ARITHMETIC, the command itself (add, sub, etc) is returned
	# Should not be called if the current command is C_RETURN
	# Return type: string
	def arg1(self):
		segments = {
			'local': 'LCL',
			'argument': 'ARG',
			'this': 'THIS',
			'that': 'THAT',
			'constant': 'constant',
			'temp': 'temp',
			'pointer': 'pointer',
			'static': 'static'
		}
		return str(segments[self.currentCommand[1]])

	# Returns current command's second argument.
	# Should only be called if curent command is:
	# C_PUSH, C_POP, C_FUNCTION, or C_CALL
	# Return type: int
	def arg2(self):
		return str(self.currentCommand[2])
	
class CodeWriter:
	# returnLabels = {}
	
	arithmeticCodes = {
		'add': ["@SP", "M=M-1", "A=M", "D=M", "A=A-1", "M=M+D"],
		'sub': ["@SP", "M=M-1", "A=M", "D=M", "A=A-1", "M=M-D"],
		'gt': ["@SP", "M=M-1", "A=M", "D=M", "A=A-1", "M=D-M"],
		'lt': ["@SP", "M=M-1", "A=M", "D=M", "A=A-1", "M=M-D"],
		'eq': ["@SP", "M=M-1", "A=M", "D=M", "@SP", "M=M-1", "A=M", "D=M-D", "@R13", "M=D", "@SP", "M=M+1", "A=M", "D=M", "@SP", "M=M-1", "A=M", "D=D-M", "@R14", "M=D", "@R13", "M=M|D", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
		'and': ["@SP", "M=M-1", "A=M", "D=M", "A=A-1", "M=M&D"],
		'or': ["@SP", "M=M-1", "A=M", "D=M", "A=A-1", "M=M|D"],
		'not': ["@SP", "A=M-1", "M=!M"],
		'neg': ["@SP", "A=M-1", "M=-M"]
	}
	commandsWritten = 0
	def __init__(self, outputfile):
		self.outputfile = outputfile
		self.gtCount = 0
		self.ltCount = 0
		self.eqCount = 0
		self.operationsCount = {
		    "lt": 0,
		    "gt": 0,
		    "eq": 0,
			"or": 0
		}
		self.currentFunc = "null"
		self.funcRetIndex = 1
	
	def writeCommands(self, commands):
		for cmd in commands:
			self.outputfile.write(cmd+'\n')
			self.commandsWritten += 1
 
 
	def setFileName(self, fileName):
		pass
	
	def writeInit(self):
		predefinedRegs = {
			  "SP":	"256",
			#  "LCL":	"300",
			#  "ARG":	"400",
			# "THIS":	"3000",
			# "THAT":	"3010"
		}

		self.writeComment("Boostrap Code")

		# for register, value in predefinedRegs.items():
		# 	self.writeCommands([f'@{value}', 'D=A', f'@{register}', 'M=D'])

		callCmds = [
			"@256", "D=A", "@SP", "M=D",
			"@300", "D=A", "@LCL", "M=D",
			"@400", "D=A", "@ARG", "M=D",
			"@3000", "D=A", "@THIS", "M=D",
			"@3010", "D=A", "@THAT", "M=D",
			# f'@{self.commandsWritten}','D=A','@SP','A=M','M=D',
			'@5', 'D=A', '@SP','M=M+D',

#    '@LCL','D=M','@SP','A=M','M=D',
# 			'@SP','M=M+1','@ARG','D=M','@SP	','A=M','M=D','@SP','M=M+1','@THIS','D=M',
# 			'@SP','A=M','M=D','@SP','M=M+1','@THAT','D=M','@SP','A=M','M=D','@SP','M=M+1',
# 			'@SP','D=M','@5','D=D-A',f'@0','D=D-A','@ARG','M=D','@SP','D=M','@LCL','M=D',
			f'@Sys.init','0;JMP'#,f'(JumpToSys.init)'
		]
		self.writeComment("call Sys.init 0")
		self.writeCommands(callCmds)
	
	def writeLabel(self, label):
		self.outputfile.write(f"\n({label})\n")

	
	def writeGoto(self, label):
		label = self.currentFunc + '$' + label
		
		self.writeComment("goto")
		self.writeCommands([f"@{label}", "0;JMP"])
	

	def writeIf(self, label):
		label = self.currentFunc + '$' + label
		cmd = ["@SP","AM=M-1","D=M",f"@{label}","D;JNE"]
		
		self.writeComment("if-goto")
		self.writeCommands(cmd)


	def writeFunction(self, functionName, numVars):
		if len(parser.currentCommand) != 3:
			print("CodeWriter.writeFunction(): pre-condition")
			print(parser.currentCommand)
			exit()
		
		self.currentFunc = parser.currentCommand[1]
		self.writeLabel(self.currentFunc)
		self.writeComment(f'function {functionName} {numVars}')
		
		for i in range(int(numVars)):
			self.writePushPop('C_PUSH', 'constant', '0')


	def writeComment(self, comment):
		self.outputfile.write(f"\n// {comment}\n")


	def writeCall(self, functionName, numArgs):
		# push returnAddress
		# self.returnLabels[]
		callCmds = [
			f'@{currentInputFileName}$ret.{self.funcRetIndex}','D=A','@SP','A=M','M=D','@SP','M=M+1','@LCL','D=M','@SP','A=M','M=D',
			'@SP','M=M+1','@ARG','D=M','@SP	','A=M','M=D','@SP','M=M+1','@THIS','D=M',
			'@SP','A=M','M=D','@SP','M=M+1','@THAT','D=M','@SP','A=M','M=D','@SP','M=M+1',
			'@SP','D=M','@5','D=D-A',f'@{numArgs}','D=D-A','@ARG','M=D','@SP','D=M','@LCL','M=D',
			f'@{functionName}','0;JMP'
		]
		self.writeComment(f"call {functionName} {numArgs}")
		self.writeCommands(callCmds)
		self.writeLabel(f'{currentInputFileName}$ret.{self.funcRetIndex}')
		
		self.funcRetIndex += 1


	def writeReturn(self):
		ret = [
				'@LCL', 'D=M', '@endFrame', 'M=D', '@5', 'D=A', '@endFrame', 'A=M-D', 'D=M', '@retAddr', 
				'M=D', '@SP', 'AM=M-1', 'D=M', '@ARG', 'A=M', 'M=D', '@ARG', 'D=M+1', '@SP', 'M=D',
				'@endFrame', 'A=M-1', 'D=M', '@THAT', 'M=D', '@2', 'D=A', '@endFrame', 'A=M-D', 'D=M',
				'@THIS', 'M=D', '@3', 'D=A', '@endFrame', 'A=M-D', 'D=M', '@ARG', 'M=D', '@4', 'D=A',
				'@endFrame', 'A=M-D', 'D=M', '@LCL', 'M=D', '@retAddr', 'A=M', '0;JMP'
			]
		self.writeComment('return')
		self.writeCommands(ret)


	# writes the assembly code that implements
	# the given command to output file
	def writeArithmetic(self, operation):
		self.writeComment(f"{operation}")

		if operation == "lt" or operation == "gt" or operation == "eq":
			self.writeLessEqGt(operation)
		elif operation == "not" or operation == "and" or operation == "add" or operation == "sub" or operation == "or" or operation == "neg":
			self.writeCommands(self.arithmeticCodes[operation])
		elif operation == "or":
			self.writeOr(operation)
	
	def writeOr(self, operation):
		trueLabel = self.getComparisonLabel(operation, "TRUE")
		falseLabel = self.getComparisonLabel(operation, "FALSE")

		part1 = [
      			f"@SP", "M=M-1", "A=M", "D=M", "@R13", "M=D", "@SP", "M=M-1", "A=M", "D=M",
           		"@R14", "M=D", "D=M", f"@{trueLabel}", "D+1;JEQ", "@R13", "D=M", f"@{trueLabel}",
              	"D+1;JEQ", "@SP", "A=M", "M=0", f"@{falseLabel}", "0;JMP"
		]
		part2 = ["@SP","A=M","M=-1"]
		part3 = ["@SP","M=M+1"]
	
		self.writeComment("or")		
  
		self.writeCommands(part1)

		self.writeLabel(trueLabel)
		self.writeCommands(part2)

		self.writeLabel(falseLabel)
		self.writeCommands(part3)

	def getComparisonLabel(self, operation, trueOrFalse):
		if trueOrFalse == "TRUE" or trueOrFalse == "FALSE":
			return f"{currentInputFileName}${operation}IF{trueOrFalse}.{self.operationsCount[operation]}"

	def writeLessEqGt(self, operation):
		trueLabel = f"{currentInputFileName}${operation}IFTRUE.{self.operationsCount[operation]}"
		falseLabel = f"{currentInputFileName}${operation}IFFALSE.{self.operationsCount[operation]}"

		part1 = [
		            "@SP","AM=M-1","D=M","@SP","AM=M-1",
		            "MD=M-D",f"@{trueLabel}","D;J"+operation.upper(),"@SP",
		            "A=M","M=0",f"@{falseLabel}","0;JMP"
		        ]
		part2 = ["@SP","A=M","M=-1"]
		part3 = ["@SP","M=M+1"]

		self.writeCommands(part1)
 
		self.writeLabel(trueLabel)
		self.writeCommands(part2)

		self.writeLabel(falseLabel)
		self.writeCommands(part3)

		self.operationsCount[operation] += 1

	# arg types: command (C_PUSH or C_POP),
	# segment (string), index (int)
	# write assembly code that implements the command
	# to the output file
	def writePushPop(self, command, segment, index):
		push = {
			"constant": [f"@{index}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"static": [f"@{currentInputFileName + '.' + index}", "D=A", f"@{segment}", "A=M+D", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"temp": [f"@{5+int(index)}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"this": [f"@THIS", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"that": [f"@THAT", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"THAT":[f"@{index}", "D=A", f"@{segment}", "A=M+D", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"LCL": [f"@{index}", "D=A", "@LCL", "A=M+D", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"],
			"ARG": [f"@{index}", "D=A", f"@{segment}", "A=M+D", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
			# "pointer": {}
		}
		
		pop = {
			"static": [f"@SP", "M=M-1", "A=M", "D=M", "@R13", "M=D", f"@{currentInputFileName + '.' + index}", "D=A", f"@{segment}", "D=M+D", "@R14", "M=D", "@R13", "D=M", "@R14", "A=M", "M=D"],
			"temp": [f"@SP", "AM=M-1", "D=M", f"@{5+int(index)}", "M=D"],
			"this": [f"@SP", "M=M-1", "A=M", "D=M", "@THIS", "M=D"],
			"that": [f"@SP", "M=M-1", "A=M", "D=M", "@THAT", "M=D"],
			"THAT": [f"@SP", "M=M-1", "A=M", "D=M", "@R13", "M=D", f"@{index}", "D=A", f"@{segment}", "D=M+D", "@R14", "M=D", "@R13", "D=M", "@R14", "A=M", "M=D"],
			"LCL": [f"@{index}", "D=A", "@LCL", "D=M+D", "@R13", "M=D", "@SP", "AM=M-1", "D=M", "@R13", "A=M", "M=D"],
			"ARG": [f"@SP", "M=M-1", "A=M", "D=M", "@R13", "M=D", f"@{index}", "D=A", f"@{segment}", "D=M+D", "@R14", "M=D", "@R13", "D=M", "@R14", "A=M", "M=D"]
		}

		self.writeComment(f"{command[2:]} {segment} {index}")
		# print("segment: " + segment)
		if segment == "pointer":
			if index == '0':
				if command == "C_PUSH":
					self.writeCommands(push["this"])
					return
				elif command == "C_POP":
					self.writeCommands(pop["this"])
					return
			elif index == '1':
				if command == "C_PUSH":
					self.writeCommands(push["that"])
					return
				elif command == "C_POP":
					self.writeCommands(pop["that"])
					return
		if command == "C_PUSH":
			self.writeCommands(push[segment])
		elif command == 'C_POP':
			self.writeCommands(pop[segment])


	def close(self):
		self.outputfile.close()


def translationLoop():
	while parser.hasMoreCommands():
		parser.advance()
		if parser.commandType() == 'C_ARITHMETIC':
			codeWriter.writeArithmetic(parser.currentCommand[0])
		elif parser.commandType() == 'C_LABEL':
			codeWriter.writeLabel(f"{codeWriter.currentFunc}$"+parser.currentCommand[1])
		elif parser.commandType() == 'C_IF':
			codeWriter.writeIf(parser.currentCommand[1])
		elif parser.commandType() == 'C_GOTO':
			codeWriter.writeGoto(parser.currentCommand[1])
		elif parser.commandType() == 'C_PUSH':
			codeWriter.writePushPop(parser.commandType(), parser.arg1(), parser.arg2())
		elif parser.commandType() == 'C_POP':
			codeWriter.writePushPop(parser.commandType(), parser.arg1(), parser.arg2())
		elif parser.commandType() == 'C_FUNCTION':
			codeWriter.writeFunction(parser.currentCommand[1], parser.currentCommand[2])
		elif parser.commandType() == 'C_RETURN':
			codeWriter.writeReturn()
		elif parser.commandType() == 'C_CALL':
			codeWriter.writeCall(parser.currentCommand[1], parser.currentCommand[2])
		else:
			print("Error: other command: " + parser.commandType())
			exit()


class Main:
	def __init__(self):
		pass
	
	def getDirName(self):
		return os.path.basename(os.path.normpath(sys.argv[1]))


main = Main()

if os.path.isdir(sys.argv[1]):
	isDir = True
	initWritten = False
	
	dirName = main.getDirName()
	outputFileName = dirName + '.asm'
	path = sys.argv[1].rstrip("/")
	path = sys.argv[1].rstrip("\\")
	of = open(os.path.join(path,outputFileName), 'w')
	codeWriter = CodeWriter(of)
	# codeWriter.writeInit()
 
	# how many .vm files?
	vmFilesInDir = 0
	for file in os.listdir(sys.argv[1]):
		if file.endswith(".vm"):
			vmFilesInDir += 1
	for file in os.listdir(sys.argv[1]):
		if file.endswith(".vm"):
			inputFileName = file[-3]
			f = open(os.path.join(path,file))
   
			parser = Parser(f)
   
			currentInputFileName = file[:-3]
   			
			if initWritten == False and vmFilesInDir > 1:
				codeWriter.writeInit()
				initWritten = True

			translationLoop()		
elif os.path.isfile(sys.argv[1]):
	# print('a')
	fullInputFileName = os.path.basename(sys.argv[1])
	currentInputFileName = fullInputFileName.partition('.')[0]
	fullOutputFileName = currentInputFileName + '.asm'
	
	f = open(sys.argv[1], 'r')
	parser = Parser(f)
	of = open(fullOutputFileName, 'w')
	codeWriter = CodeWriter(of)
 
	translationLoop()
else:
	print("neither")

codeWriter.close()