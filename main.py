import math
import numpy as np
import argparse
from rply import LexerGenerator, ParserGenerator
from rply.token import BaseBox

class Number(BaseBox):
    def __init__(self, value):
        self.value = value

    def eval(self):
        return self.value

class BinaryOp(BaseBox):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Add(BinaryOp):
    def eval(self):
        return self.left.eval() + self.right.eval()

class Sub(BinaryOp):
    def eval(self):
        return self.left.eval() - self.right.eval()

class Mul(BinaryOp):
    def eval(self):
        return self.left.eval() * self.right.eval()

class Div(BinaryOp):
    def eval(self):
        return self.left.eval() / self.right.eval()
    

class Calculator():
    def __init__(self) -> None:
        self.lexer = None
        self.parser = None
        self.Build()
        self.Parser()
        
    def Build(self):
        lg = LexerGenerator()

        lg.add('NUMBER', r'\d+')
        lg.add('PLUS', r'\+')
        lg.add('MINUS', r'-')
        lg.add('MUL', r'\*')
        lg.add('DIV', r'/')
        lg.add('OPEN_PARENS', r'\(')
        lg.add('CLOSE_PARENS', r'\)')

        lg.ignore('\s+')

        self.lexer = lg.build()
    
    def Parser(self):
        pg = ParserGenerator(
            # A list of all token names, accepted by the parser.
            ['NUMBER', 'OPEN_PARENS', 'CLOSE_PARENS',
            'PLUS', 'MINUS', 'MUL', 'DIV'
            ],
            # A list of precedence rules with ascending precedence, to
            # disambiguate ambiguous production rules.
            precedence=[
                ('left', ['PLUS', 'MINUS']),
                ('left', ['MUL', 'DIV'])
            ]
        )
        @pg.production('expression : NUMBER')
        def expression_number(p):
            # p is a list of the pieces matched by the right hand side of the
            # rule
            return Number(int(p[0].getstr()))

        @pg.production('expression : OPEN_PARENS expression CLOSE_PARENS')
        def expression_parens(p):
            return p[1]

        @pg.production('expression : expression PLUS expression')
        @pg.production('expression : expression MINUS expression')
        @pg.production('expression : expression MUL expression')
        @pg.production('expression : expression DIV expression')
        def expression_binop(p):
            left = p[0]
            right = p[2]
            if p[1].gettokentype() == 'PLUS':
                return Add(left, right)
            elif p[1].gettokentype() == 'MINUS':
                return Sub(left, right)
            elif p[1].gettokentype() == 'MUL':
                return Mul(left, right)
            elif p[1].gettokentype() == 'DIV':
                return Div(left, right)
            else:
                raise AssertionError('Oops, this should not be possible!')

        self.parser = pg.build()
        
    def Calculate(self, argument):
        print(self.parser.parse(self.lexer.lex(sys.argv[1])).eval())

import sys
def main():
    cal = Calculator()
    cal.Calculate(sys.argv[1])

if __name__ == "__main__":
    main()