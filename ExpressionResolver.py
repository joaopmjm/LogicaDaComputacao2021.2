from os import chmod, remove, truncate
from typing import Counter, Match, Type, ValuesView
from typing_extensions import IntVar
from rply import LexerGenerator, ParserGenerator
from rply.token import BaseBox
from Calculator import Calculator

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
                return BinExp(p[1].getstr(),left, right)
            else:
                raise AssertionError('Oops, this should not be possible!')
        
        self.parser = pg.build()
    
    def Calculate(self, argument):
        return self.parser.parse(self.lexer.lex(argument))