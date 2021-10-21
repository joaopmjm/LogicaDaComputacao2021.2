from os import chmod, remove, replace, truncate
from typing import Counter, Match, Type, ValuesView
from typing_extensions import IntVar
from rply import LexerGenerator, ParserGenerator
from rply.token import BaseBox
import command_tools as ct
import sys

comment_Init = "/*"
comment_Final = "*/"
start_bracket = '{'
end_bracket = '}'
ADD = '+'
SUB = '-'
MUL = '*'
DIV = '/'
POT = '^'
AND = '&&'
OR = '||'
EQ = '=='
DIF = '!='
GET = '>='
LET = '<='
GT = '>'
LT = '<'

class Node(BaseBox):
    def __init__(self, value):
        self.value = value
        self.children = []

    def eval(self):
        return self.value

class IntVal(Node):
    def __init__(self, value):
        self.value = value
    
    def eval(self):
        return self.value

class UnOp(Node):
    def __init__(self, value, child):
        self.value = value
        self.children = [child]

class BinOp(Node):
    def __init__(self, value,left, right):
        self.value = value
        self.children = [left, right]

    def eval(self):
        return {
            SUB:self.children[0].eval() - self.children[1].eval(),
            ADD:self.children[0].eval() + self.children[1].eval(),
            MUL:self.children[0].eval() * self.children[1].eval(),
            DIV:self.children[0].eval() / self.children[1].eval(),
            POT:self.children[0].eval() ** self.children[1].eval()
        }[self.value]

class BinExp(Node):
    def __init__(self, value, left, right):
        self.value = value
        self.children = [left, right]
    def eval(self):
        return {
            AND:self.children[0].eval() and self.children[1].eval(),
            OR:self.children[0].eval() or self.children[1].eval(),
            EQ:self.children[0].eval() == self.children[1].eval(),
            DIF:self.children[0].eval() != self.children[1].eval(),
            GET:self.children[0].eval() >= self.children[1].eval(),
            LET:self.children[0].eval() <= self.children[1].eval(),
            GT:self.children[0].eval() > self.children[1].eval(),
            LT:self.children[0].eval() < self.children[1].eval(),
        }[self.value]
        
class BinExpression():
    def __init__(self):
        self.lexer = None
        self.parser = None
        self.Build()
        self.Parser()

    def Build(self):
        lg = LexerGenerator()

        lg.add('NUMBER', r'\d+')
        lg.add('AND', r'\[&&]')
        lg.add('OR', r'\|\|')
        lg.add('EQ', r'\==')
        lg.add('DIF', r'\!=')
        lg.add('GET', r'\>=')
        lg.add('LET', r'\<=')
        lg.add('GT', r'\>')
        lg.add('LT', r'\<')
        lg.add('OPEN_PARENS', r'\(')
        lg.add('CLOSE_PARENS', r'\)')

        lg.ignore('\s+')

        self.lexer = lg.build()
    
    def Parser(self):
        pg = ParserGenerator(
            ['NUMBER', 'OPEN_PARENS', 'CLOSE_PARENS', 'AND', 'OR', 'EQ', 
             'DIF', 'GET', 'LET', 'GT', 'LT'
            ],
            precedence=[
                ('left', ['AND', 'OR', 'EQ', 
                    'DIF', 'GET', 'LET']),
                ('left', ['GT', 'LT'])
            ]
        )
        
        @pg.production('expression : NUMBER NUMBER')
        @pg.production('expression : AND AND')
        @pg.production('expression : OR OR')
        @pg.production('expression : EQ EQ')
        @pg.production('expression : DIF DIF')
        @pg.production('expression : GET GET')
        @pg.production('expression : LET LET')
        @pg.production('expression : GT GT')
        @pg.production('expression : LT LT')        
        def expression_exception(p):
            print(p[0].getstr(), p[1].getstr())
            print(p[0].gettokentype(), p[1].gettokentype())
            raise ValueError

        @pg.production('expression : NUMBER')
        def expression_number(p):
            return IntVal(int(p[0].getstr()))
        
        @pg.production('expression : OPEN_PARENS expression CLOSE_PARENS')
        def expression_parens(p):
            return p[1]           
        
        @pg.production('expression : expression AND expression')
        @pg.production('expression : expression OR expression')
        @pg.production('expression : expression EQ expression')
        @pg.production('expression : expression DIF expression')
        @pg.production('expression : expression GET expression')
        @pg.production('expression : expression LET expression')
        @pg.production('expression : expression GT expression')
        @pg.production('expression : expression LT expression')
        def expression_binop(p):
            left = p[0]
            right = p[2]
            if p[1].gettokentype() in ['AND', 'OR', 'EQ', 'DIF', 'GET', 'LET', 'GT', 'LT']:
                return BinExp(p[1].gettokentype(),left, right)
            else:
                raise AssertionError('Oops, this should not be possible!')
        
        self.parser = pg.build()
    
    def Calculate(self, argument):
      return self.parser.parse(self.lexer.lex(argument))
    
class Calculator():
    def __init__(self):
        self.lexer = None
        self.parser = None
        self.Build()
        self.Parser()
        
    def Build(self):
        lg = LexerGenerator()

        lg.add('NUMBER', r'\d+')
        lg.add('PLUS', r'\+([+-]+)?')
        lg.add('MINUS', r'\-([+-]+)?')
        lg.add('MUL', r'\*')
        lg.add('DIV', r'/')
        lg.add('POT', r'\^')
        lg.add('OPEN_PARENS', r'\(')
        lg.add('CLOSE_PARENS', r'\)')

        lg.ignore('\s+')

        self.lexer = lg.build()
    
    def Parser(self):
        pg = ParserGenerator(
            ['NUMBER', 'OPEN_PARENS', 'CLOSE_PARENS',
            'PLUS', 'MINUS', 'MUL', 'DIV', 'POT'
            ],
            precedence=[
                ('left', ['PLUS', 'MINUS']),
                ('left', ['MUL', 'DIV']),
                ('left', ['POT'])
            ]
        )
        @pg.production('expression : PLUS expression')
        @pg.production('expression : MINUS expression')
        def expression_unary(p):
            left = IntVal(0)             
            right = p[1]
            if p[0].gettokentype() == 'PLUS':
                if len(p[0].getstr()) > 1:
                    neg = False
                    for c in p[0].getstr():
                        if c == '-':
                            neg = not neg
                else:
                    return BinOp(ADD,left, right)
                if neg:
                    return BinOp(SUB,left, right)
                return BinOp(ADD, left, right)
            elif p[0].gettokentype() == 'MINUS':
                if len(p[0].getstr()) > 1:
                    neg = False
                    for c in p[0].getstr():
                        if c == '-':
                            neg = not neg
                else:
                    return BinOp(SUB,left, right)
                if neg:
                    return BinOp(SUB,left, right)
                return BinOp(ADD,left, right)
        
        @pg.production('expression : NUMBER NUMBER')
        def expression_exception(p):
            raise ValueError

        @pg.production('expression : NUMBER')
        def expression_number(p):
            return IntVal(int(p[0].getstr()))
        
        @pg.production('expression : OPEN_PARENS expression CLOSE_PARENS')
        def expression_parens(p):
            return p[1]            
        
        @pg.production('expression : expression PLUS expression')
        @pg.production('expression : expression MINUS expression')
        @pg.production('expression : expression MUL expression')
        @pg.production('expression : expression DIV expression')
        @pg.production('expression : expression POT expression')
        def expression_binop(p):
            left = p[0]             
            right = p[2]
            if p[1].gettokentype() == 'PLUS':
                if len(p[1].getstr()) > 1:
                    neg = False
                    for c in p[1].getstr():
                        if c == '-':
                            neg = not neg
                else:
                    return BinOp(ADD,left, right)
                if neg:
                    return BinOp(SUB,left, right)
                return BinOp(ADD,left, right)
            elif p[1].gettokentype() == 'MINUS':
                if len(p[1].getstr()) > 1:
                    neg = False
                    for c in p[1].getstr():
                        if c == '-':
                            neg = not neg
                else:
                    return BinOp(SUB,left, right)
                if neg:
                    return BinOp(SUB,left, right)
                return BinOp(ADD, left, right)
            elif p[1].gettokentype() == 'MUL':
                return BinOp(MUL,left, right)
            elif p[1].gettokentype() == 'DIV':
                return BinOp(DIV,left, right)
            elif p[1].gettokentype() == 'POT':
                return BinOp(POT,left, right)
            else:
                raise AssertionError('Oops, this should not be possible!')
        
        self.parser = pg.build()
    
    def RemoveSpaces(self, argument):
        SPACE = " "
        while argument[0] == SPACE:
            argument = argument[1:len(argument)]
        while argument[-1] == SPACE:
            argument = argument[0:len(argument)-1]
        ops = {
            0:['+','-'],
            1:['*','/','^']
        }
        while argument.find(SPACE*2, 0, len(argument)) != -1:
            argument = argument.replace(SPACE*2, SPACE)
        
        c = 0
        while c < len(argument):
            if argument[c] == SPACE:
                if ((argument[c-1] in ops[0] and argument[c+1] in ops[0]) or \
                (argument[c-1] in ops[1] and argument[c+1] in ops[1])):
                    argument = argument[0 : c :] + argument[c + 1 : :]
            c += 1
        return argument
    
    def RemoveComments(self, argument):
        i = 0
        open = False
        while i < len(argument)-2:
            if argument[i:i+2] == comment_Init:
                init = i
                open = True
                i += 2
                while (argument[i-2:i] != comment_Final) and i < len(argument):
                    i += 1
                if argument[i-2:i] == comment_Final:
                    open = False
                argument = argument[0:init] + argument[i:len(argument)]
                i = 0
            else:
                i += 1
        if open:
            raise TypeError
        
        return self.RemoveSpaces(argument)
    
    def Calculate(self, argument):
        return self.parser.parse(self.lexer.lex(self.RemoveComments(argument)))        

class Program():
    def __init__(self):
        self.commands = []
        self.variables = {}
        self.cal = Calculator()
        self.binExp = BinExpression()
        self.ReservedNames = ["if","while","println","input"]
    
    def Build(self, program):
        program = program.replace("\n", "")
        program = self.RemoveComments(program)
        if(';' not in program): raise ValueError
        self.commands = program.split(';')
        self.PrepareInput()
        
    def Run(self, prog):
        self.Build(prog)
        i = 0
        self.Runner(i)
    
    def Runner(self, i):
        while i < len(self.commands):
            command = self.commands[i]
            if(self.GetCommandType(command) == "println"):
                self.Println(command)
            elif(command == "}"):
                return i
            elif('=' in command):
                self.Attribuition(command)
            elif not command.isspace() and len(command)>0:
                print("Error with command",command)
                raise ValueError
            i += 1
            
    def GetCommandType(self, command):
        command_type = None
        command = ct.RemoveSpaces(command)
        if(command.startswith("if")): command_type = "if"
        if(command.startswith("while")): command_type = "while"
        if(command.startswith("println")): command_type = "println"
        if command_type != None:
            for key in ["if","while","println"]:
                command = command.replace(key,"")
            if(command[0] != "(" or command[-1] != ")"): raise SyntaxError
        return command_type

    def Attribuition(self, command):
        var_name, expression = command.split('=')
        if var_name[0].isnumeric(): raise ValueError
        var_name = var_name.replace(' ','')
        expression = ct.RemoveSpaces(expression)
        if(expression.startswith("readln")):
            self.variables[var_name] = int(input())
        else:    
            self.variables[var_name] = self.CalculateExpression(self.PrepareExpression(expression))
        for k in sorted(self.variables, key=len, reverse=True):
            self.variables[k] = self.variables[k]
    
    def WhileCommand(self, i):
        command = self.commands[i]
        if(not self.ParentesisEquilized(command)): raise ValueError
        if(command.endswith("{")):
            while(self.binExp.Calculate(self.GetExpression(i)).eval()):
                i = self.Runner(i)
            return i
        else:
            raise ValueError
        
    def IfCommand(self, i):
        command = self.commands[i]
        if(not self.ParentesisEquilized(command)): raise ValueError
        if(command.endswith("{")):
            if(self.binExp.Calculate(self.GetExpression(i)).eval()):
                i = self.Runner(i)
            return i
        else:
            raise ValueError
    
    def Println(self, command):
        command = command[7:]
        if(command[0] == '(' and command[-1] == ')'):
            command = self.ReplaceVars(command[1:-1])
            print(self.CalculateExpression(command))
        else:
            raise ValueError
    
    def GetExpression(self, i):
        start = 0
        end = 0
        for j in range(len(self.commands[i])):
            if self.commands[j] == "(":
                start = j
                break
        for j in range(len(self.commands[i]), 0, -1):
            if self.commands[j] == ")":
                end = j
                break
        return self.ReplaceVars(self.commands[i][start+1:end])
    
    def ReplaceVars(self, command):
        for var in self.variables.keys():
            command = command.replace(var, str(self.variables[var]))
        return command
            
    
    def ParentesisEquilized(command):
        i = 0
        for c in command:
            if c == "(": i+=1
            if c == ")": i-=1
        if i == 0: return True
        return False
    
    def JumpOrContinue(self, i):
        exp = self.GetExpression(i)
        brackets = 1
        c = i+1
        while brackets > 0:
            if end_bracket in self.commands[i]:
                brackets -= 1
            if start_bracket in self.commands[i]:
                brackets += 1
            c += 1
            if c >= len(self.commands):
                raise TabError
        if(self.binExp.Calculate(exp).eval()):
            return i+1
        return c
    
    def PrepareInput(self):
        to_be_removed = []
        for i in range(len(self.commands)):
            if self.commands[i].isspace() and len(self.commands[i])<=0: 
                to_be_removed.append(i)
            else:
                while self.commands[i].startswith(' '):
                    self.commands[i] = self.commands[i][1:]
        for i in range(len(to_be_removed)-1,0,-1):
            del self.commands[to_be_removed[i]]
            
    def RemoveComments(self, argument):
        i = 0
        open = False
        while i < len(argument)-2:
            if argument[i:i+2] == comment_Init:
                init = i
                open = True
                i += 2
                while (argument[i-2:i] != comment_Final) and i < len(argument):
                    i += 1
                if argument[i-2:i] == comment_Final:
                    open = False
                argument = argument[0:init] + argument[i:len(argument)]
                i = 0
            else:
                i += 1
        if open:
            raise TypeError
        
        return argument
    
    def PrepareExpression(self, expression):
        for var in self.variables.keys():
            if var in expression:
                expression = expression.replace(var, str(self.variables[var]))
        return expression
                
    def CalculateExpression(self, expression):
        root = self.cal.Calculate(expression)
        return int(root.eval())
    
def main():
    prog = Program()
    prog.Run(sys.argv[1])

if __name__ == "__main__":
    main()