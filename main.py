from os import chmod, remove, replace, truncate
from typing import Counter, Match, Type, ValuesView
from typing_extensions import IntVar
from rply import LexerGenerator, ParserGenerator
from rply.token import BaseBox
import command_tools as ct
from Calculator import *
from ExpressionResolver import *
import sys

class Program():
    def __init__(self):
        self.commands = []
        self.variables = {}
        self.cal = Calculator()
        self.expResolver = ExpressionResolver()
        self.ReservedNames = ["if","while","println","readln"]
    
    def Build(self, program):
        program = program.replace("\n", "")
        program = self.RemoveComments(program)
        if(';' not in program): raise ValueError
        blocos = program.split('{')
        for bloco in blocos:
            for command in bloco.split(';'):
                self.commands.append(command)
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
            elif(self.GetCommandType(command) == "if"):
                i = self.IfCommand(i)
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
    
    def IfCommand(self, i):
        command = self.commands[i]
        if(not ct.ParentesisEquilized(command)): raise ValueError
        if(self.expResolver.Calculate(self.GetExpression(i)).eval()):
            return self.Runner(i+1)
        else:
            return self.GetEndOfBrackets(i)
        return i
    
    def WhileCommand(self, i):
        command = self.commands[i]
        if(not ct.ParentesisEquilized(command)): raise ValueError
        if(command.endswith("{")):
            while(self.expResolver.Calculate(self.GetExpression(i)).eval()):
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
    
    def GetEndOfBrackets(self, i):
        brackets_opened = 1
        i += 1
        while brackets_opened > 0:
            if i >= len(self.commands):
                print(self.commands, i, len(self.commands))
                raise IndentationError
            if any(command in ["if", "while"] for command in self.commands[i]): brackets_opened += 1
            if "}" in ct.RemoveSpaces(self.commands[i]): brackets_opened -= 1
            i += 1
        return i
    
    def GetExpression(self, i):
        return self.ReplaceVars(self.commands[i][self.commands[i].index('(')+1:-1])
    
    def ReplaceVars(self, command):
        for var in self.variables.keys():
            command = command.replace(var, str(self.variables[var]))
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