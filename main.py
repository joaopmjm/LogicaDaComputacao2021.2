from os import chmod, remove, replace, truncate
import command_tools as ct
from typing import Counter, Match, Type, ValuesView
from typing_extensions import IntVar
from rply.token import BaseBox
# from ExpressionResolver import *
import sys

ST={}
variables = {}
in_loop = False

from rply import LexerGenerator, ParserGenerator
from rply.token import BaseBox

comment_Init = "/*"
comment_Final = "*/"
start_bracket = '{'
end_bracket = '}'
NOT = '!'
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

class Not(Node):
  def __init__(self, value):
    self.value = value
  def eval(self):
    return not self.value

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
        
class ExpressionResolver():
    def __init__(self):
        self.lexer = None
        self.parser = None
        self.calculator = Calculator()
        self.Build()
        self.Parser()

    def Build(self):
        lg = LexerGenerator()

        lg.add('NUMBER', r'[+-]?\d+')
        lg.add('VARIABLE', r'[a-zA-z]([a-zA-z0-9]*)')
        lg.add('NOT', r'\!')
        lg.add('AND', r'\&\&')
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
            ['NUMBER', 'VARIABLE', 'OPEN_PARENS', 'CLOSE_PARENS','NOT', 'AND', 'OR', 'EQ', 
             'DIF', 'GET', 'LET', 'GT', 'LT'
            ],
            precedence=[
                ('left', ['NOT']),
                ('left', ['AND', 'OR', 'EQ', 
                    'DIF', 'GET', 'LET']),
                ('left', ['GT', 'LT'])
            ]
        )
        
        @pg.production('expression : NUMBER NUMBER')
        @pg.production('expression : VARIABLE VARIABLE')
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
        
        @pg.production('expression : VARIABLE')
        def expression_variable(p):
            if p[0].getstr() in variables.keys(): 
                return IntVal(int(variables[p[0].getstr()]))     
            raise AssertionError("Variable not declared")   
        
        @pg.production('expression : OPEN_PARENS expression CLOSE_PARENS')
        def expression_parens(p):
            return p[1]           
        
        @pg.production('expression : NOT expression')
        def expression_not(p):
          return Not(p[1].eval())
        
        @pg.production('expression : expression AND expression')
        @pg.production('expression : expression OR expression')
        @pg.production('expression : expression EQ expression')
        @pg.production('expression : expression DIF expression')
        @pg.production('expression : expression GET expression')
        @pg.production('expression : expression LET expression')
        @pg.production('expression : expression GT expression')
        @pg.production('expression : expression LT expression')
        def expression_binop(p):
            if p[0].getstr() in variables.keys(): 
                left = variables[p[0].getstr()]
                write_if(f"lod 0 {p[0].getstr()}")
            else:
                left = p[0]
                write_if(f"lit 0 {left}")
            if p[0].getstr() in variables.keys(): 
                left = variables[p[2].getstr()]
                write_if(f"lod 1 {p[2].getstr()}")
            else:
                right = p[2]
                write_if(f"lit 1 {right}")
            op = ['AND', 'OR', 'EQ', 'DIF', 'GET', 'LET', 'GT', 'LT']
            if p[1].gettokentype() in op:
                write_if(f"cmp {op.index(p[1].gettokentype())} END")
                return BinExp(p[1].getstr(),left, right)
            else:
                raise AssertionError('Oops, this should not be possible!')
        
        self.parser = pg.build()
    
    def Calculate(self, argument):
        return self.parser.parse(self.lexer.lex(argument))

comment_Init = "/*"
comment_Final = "*/"
start_bracket = '{'
end_bracket = '}'
ADD = '+'
SUB = '-'
MUL = '*'
DIV = '/'
POT = '^'
ST = {}

def write_if(text):
    if not in_loop:
        print(text)
        print("\n")

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
        lg.add('VARIABLE', r'[a-zA-z]([a-zA-z0-9]*)')

        lg.ignore('\s+')

        self.lexer = lg.build()
    
    def Parser(self):
        pg = ParserGenerator(
            ['NUMBER','VARIABLE', 'OPEN_PARENS', 'CLOSE_PARENS',
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
            if p[1].getstr().isnumeric():
                    right = p[1]
            else:
                if p[0] not in variables.keys(): 
                    raise AssertionError(f"Variable {p[0]} not inicialized")
                right = variables[p[0]]
                write_if(f"lod 0 {p[0]}\n")
            write_if(f"lit 0 {right}")
            write_if("opr 0 1")
            if p[0].gettokentype() == 'PLUS':
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
        @pg.production('expression : VARIABLE NUMBER')
        @pg.production('expression : NUMBER VARIABLE')
        def expression_exception(p):
            raise ValueError

        @pg.production('expression : NUMBER')
        def expression_number(p):
            return IntVal(int(p[0].getstr()))
        
        @pg.production('expression : VARIABLE')
        def expression_number(p):
            return IntVal(int(variables[p[0].getstr()]))
        
        @pg.production('expression : OPEN_PARENS expression CLOSE_PARENS')
        def expression_parens(p):
            return p[1]            
        
        @pg.production('expression : expression PLUS expression')
        @pg.production('expression : expression MINUS expression')
        @pg.production('expression : expression MUL expression')
        @pg.production('expression : expression DIV expression')
        @pg.production('expression : expression POT expression')
        def expression_binop(p):
            if type(p[0].eval()) == int:
                left = p[0]
                write_if(f"lit 0 {left.eval()}\n")
            else:
                if p[0] not in variables.keys(): 
                    raise AssertionError(f"Variable {p[0]} not inicialized")
                left = variables[p[0]]
                write_if(f"lod 0 {p[0]}\n")
            if type(p[2].eval()) == int:
                right = p[2]
                write_if(f"lit 0 {right.eval()}\n")
            else:
                if p[2] not in variables.keys(): 
                    raise AssertionError(f"Variable {p[2]} not inicialized")
                left = variables[p[2]]
                write_if(f"lod 0 {p[2]}\n")
            if p[1].gettokentype() == 'PLUS':
                write_if("opr 0 2\n")
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
                write_if("opr 0 3\n")
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
                write_if("opr 0 4\n")
                return BinOp(MUL,left, right)
            elif p[1].gettokentype() == 'DIV':
                write_if("opr 0 5\n")
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
class Visitor(object):
  pass

class SymbolTable(Visitor):
    def visit_prog(self, prog):
        prog.decls.accept(self)
        
    def visit_vardecls(self, d):
        d.decl.accept(self)
        if d.decls!=None:
          d.decls.accept(self)

    def visit_vardecl(self, d):
        ST[d.id]=d.tp

class Prog(BaseBox):
    def __init__(self, decls,atrib):
        self.decls = decls
        self.atrib = atrib

    def accept(self, visitor):
        visitor.visit_prog(self)

class VarDecls(BaseBox):
    def __init__(self, decl,decls):
        self.decl = decl
        self.decls = decls

    def accept(self, visitor):
        visitor.visit_vardecls(self)

class VarDecl(BaseBox):
    def __init__(self, id,tp):
        self.id = id
        self.tp = tp
        
    def accept(self, visitor):
        visitor.visit_vardecl(self)

class Atrib(BaseBox):
    def __init__(self, id,expr):
        self.id = id
        self.expr = expr

    def accept(self, visitor):
        visitor.visit_atrib(self)

class Expr(BaseBox):
    def accept(self, visitor):
        method_name = 'visit_{}'.format(self.__class__.__name__.lower())
        visit = getattr(visitor, method_name)
        visit(self)

class Decorator(Visitor):

    def visit_prog(self, i):
        i.atrib.accept(self)

    def visit_atrib(self, i):
        if i.id in ST:
          i.id_decor_type=ST[i.id]
        else:
          raise AssertionError('id not declared')
        i.expr.accept(self)
        i.expr_decor_type=i.expr.decor_type

    def visit_id(self, i):
        if i.value in ST:
          i.decor_type=ST[i.value]
        else:
          raise AssertionError('id not declared')


    def visit_number(self, i):
        i.decor_type="int"
        

    def visit_add(self, a):
        a.left.accept(self)
        a.right.accept(self)
        if a.left.decor_type=="int" and a.right.decor_type=="int":
          a.decor_type="int"
          

    def visit_sub(self, a):
        a.left.accept(self)
        a.right.accept(self)
        if a.left.decor_type=="int" and a.right.decor_type=="int":
          a.decor_type="int"

    def visit_mul(self, a):
        a.left.accept(self)
        a.right.accept(self)
        if a.left.decor_type=="int" and a.right.decor_type=="int":
          a.decor_type="int"

    def visit_div(self, a):
        a.left.accept(self)
        a.right.accept(self)
        if a.left.decor_type=="int" and a.right.decor_type=="int":
          a.decor_type="int"

class TypeVerifier(Visitor):

    def visit_prog(self, i):
        i.atrib.accept(self)

    def visit_atrib(self, i):
        if i.id_decor_type!=i.expr_decor_type:
          raise AssertionError('type error')

    def visit_add(self, a):
        if a.left.decor_type != a.right.decor_type:
          raise AssertionError('type error')
          

    def visit_sub(self, a):
        if a.left.decor_type != a.right.decor_type:
          raise AssertionError('type error')

    def visit_mul(self, a):
        if a.left.decor_type != a.right.decor_type:
          raise AssertionError('type error')

    def visit_div(self, a):
        if a.left.decor_type != a.right.decor_type:
          raise AssertionError('type error')

class IntermediateCode(Visitor):

  def visit_prog(self, i):
    i.atrib.accept(self)
    
  def visit_atrib(self, i):
    i.expr.accept(self)
        

  def visit_id(self, i):
    print("lod 0",i.value,"\n")


  def visit_number(self, i):
    print("lit 0",i.value,"\n")
        

  def visit_add(self, a):
    a.left.accept(self)
    a.right.accept(self)
    print("opr 0 2\n")
          

  def visit_sub(self, a):
    a.left.accept(self)
    a.right.accept(self)
    print("opr 0 3\n")

  def visit_mul(self, a):
    a.left.accept(self)
    a.right.accept(self)
    print("opr 0 4\n")

  def visit_div(self, a):
    a.left.accept(self)
    a.right.accept(self)
    print("opr 0 5\n")

class Program():
    def __init__(self):
        self.commands = []
        self.cal = Calculator()
        self.expResolver = ExpressionResolver()
        self.ReservedNames = ["if","while","println","readln", "for"]
    
    def Build(self, program):
        program = program.replace("\n", "")
        program = self.RemoveComments(program)
        if(';' not in program): raise ValueError
        blocos = program.split('{')
        for bloco in blocos:
            if ct.RemoveSpaces(bloco).startswith("for"):
                self.commands.append(ct.RemoveSpaces(bloco))
            else:
                for command in bloco.split(';'):
                    command = ct.RemoveSpaces(command)
                    if command.startswith("}"): 
                        while command.startswith("}"):
                            self.commands.append("}")
                            command = ct.RemoveSpaces(command[1:])
                        if not command == '':
                            self.commands.append(command)
                    else:
                        self.commands.append(command)
        self.PrepareInput()
        
    def Run(self, prog):
        self.Build(prog)
        self.Runner()
    
    def Runner(self, i=0):
        while i < len(self.commands):
            command = self.commands[i]
            if(self.GetCommandType(command) == "println"):
                self.Println(command)
            elif(self.GetCommandType(command) == "if"):
                i = self.IfCommand(i)
            elif(self.GetCommandType(command) == "while"):
                i = self.WhileCommand(i)
            elif(self.GetCommandType(command) == "for"):
                i = self.ForCommand(i)
            elif(command == "}"):
                return i
            elif('=' in command):
                self.Attribuition(command)
            elif command.startswith("int") or command.startswith("string"):
                self.Attribuition(command + "= 0")
            elif not command.isspace() and len(command)>0:
                print("Error with command",command)
                raise ValueError
            i += 1
    
    def instruction(self, command):
        if(self.GetCommandType(command) == "println"):
            self.Println(command)
        elif('=' in command):
            self.Attribuition(command)
        elif not command.isspace() and len(command)>0:
            print("Error with command",command)
            raise ValueError
            
    def GetCommandType(self, command):
        command_type = None
        possible_commands = ["if","while","println","for"]
        command = ct.RemoveSpaces(command)
        for pc in possible_commands:
            if(command.startswith(pc)): command_type = pc
        if command_type != None:
            for key in possible_commands:
                command = command.replace(key,"")
            command = ct.RemoveSpaces(command)
            if(command[0] != "(" or command[-1] != ")"): raise SyntaxError
        return command_type

    def Attribuition(self, command):
        var_name, expression = command.split('=')
        tipo = ""
        var_name = ct.RemoveSpaces(var_name)
        if var_name.startswith("int") or var_name.startswith("string"):
            tipo, var_name = var_name.split(" ")
        if var_name[0].isnumeric(): raise ValueError
        var_name = var_name.replace(' ','')
        tipo = tipo.replace(' ','')
        expression = ct.RemoveSpaces(expression)
        if not tipo in ["int","string"]:
            if var_name not in variables.keys():
                raise NameError
        if expression.startswith("readln"):
            variables[var_name] = int(input())
            ST[var_name] = VarDecl(variables[var_name], "int")
        else:
            if tipo == "int":
                variables[var_name] = self.CalculateExpression(expression)
                ST[var_name] = VarDecl(variables[var_name], "int")
            else:
                variables[var_name] = expression
                ST[var_name] = VarDecl(variables[var_name], "string")
        write_if(f"sto 0 {var_name}")
        for k in sorted(variables, key=len, reverse=True):
            variables[k] = variables[k]
            
    
    def IfCommand(self, i):
        command = self.commands[i]
        if(not ct.ParentesisEquilized(command)): raise ValueError
        end = self.GetEndOfBrackets(i)    
        self.expResolver.Calculate(ct.GetIfExpression(command))
        if ct.RemoveSpaces(self.commands[end+1]).startswith("else"):
            write_if("jcm 0 ELSE")
        if ct.IsBracketlessIf(command)[0]:
            self.instruction(ct.IsBracketlessIf(command)[1])
            i+=1
            return i
        i = self.Runner(i+1)
        self.expResolver.Calculate(ct.GetIfExpression(command))
        write_if("jcm 0 CONT")
        if ct.RemoveSpaces(self.commands[end+1]).startswith("else"):
            write_if("ELSE:")
            i = self.Runner(i+1)
        write_if("CONT:")
        return i
    
    def WhileCommand(self, i):
        command = self.commands[i]
        if(not ct.ParentesisEquilized(command)): raise ValueError
        start = i+1
        write_if("LOOP:")
        self.Runner(start)
        self.expResolver.Calculate(self.GetExpression(self.commands[i]))
        write_if("jcm 0 LOOP")
        return self.GetEndOfBrackets(i)

    def ForCommand(self, i):
        command = self.commands[i]
        self.Attribuition(self.GetExpression(command, True).split(";")[0])
        write_if("FOR:")
        self.Runner(i+1)
        self.instruction(self.GetExpression(command, True).split(";")[2])
        self.expResolver.Calculate(self.GetExpression(command).split(";")[1])
        return self.GetEndOfBrackets(i)
        
    def Println(self, command):
        command = command[7:]
        if(command[0] == '(' and command[-1] == ')'):
            # command = self.ReplaceVars(command[1:-1])
            print(self.CalculateExpression(command[1:-1]))
        else:
            raise ValueError            
    
    def GetEndOfBrackets(self, i):
        brackets_opened = 1
        i += 1
        while brackets_opened > 0:
            if i >= len(self.commands):
                raise IndentationError
            elif "if" in self.commands[i] or "while" in self.commands[i]:
                brackets_opened += 1
            elif "}" in ct.RemoveSpaces(self.commands[i]): brackets_opened -= 1
            i += 1
        return i-1
    
    def GetExpression(self, command, varless=False):
        if varless:
            return command[command.index('(')+1:-1]
        # return self.ReplaceVars(command[command.index('(')+1:-1])
        return command[command.index('(')+1:-1]
    
    def ReplaceVars(self, command):
        for var in variables.keys():
            command = command.replace(var, str(variables[var]))
        return command
    
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
                
    def CalculateExpression(self, expression):
        root = self.cal.Calculate(expression)
        return int(root.eval())
    
def main():
    prog = Program()
    prog.Run(sys.argv[1])

if __name__ == "__main__":
    main()