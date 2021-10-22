from rply import LexerGenerator, ParserGenerator
from rply.token import BaseBox

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