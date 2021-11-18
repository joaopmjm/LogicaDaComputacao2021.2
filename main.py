from os import chmod, remove, replace, truncate
import command_tools as ct
from Calculator import *
from typing import Counter, Match, Type, ValuesView
from typing_extensions import IntVar
from rply.token import BaseBox
from ExpressionResolver import *
import sys

ST={}

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

class Program():
    def __init__(self):
        self.commands = []
        self.variables = {}
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
        if var_name[0].isnumeric(): raise ValueError
        var_name = var_name.replace(' ','')
        expression = ct.RemoveSpaces(expression)
        if not var_name.startswith("int") or not var_name.startswith("string"):
            if var_name not in self.variables.keys():
                raise NameError
        if expression.startswith("readln"):
            self.variables[var_name] = int(input())
        else:    
            self.variables[var_name] = self.CalculateExpression(self.ReplaceVars(expression))
        for k in sorted(self.variables, key=len, reverse=True):
            self.variables[k] = self.variables[k]
    
    def IfCommand(self, i):
        command = self.commands[i]
        if(not ct.ParentesisEquilized(command)): raise ValueError
        end = self.GetEndOfBrackets(i)
        if ct.IsBracketlessIf(command)[0]:
            if self.expResolver.Calculate(ct.GetIfExpression(command)).eval():
                self.instruction(ct.IsBracketlessIf(command)[1])
            return i
        elif self.expResolver.Calculate(self.GetExpression(self.commands[i])).eval():
            i = self.Runner(i+1)
            if ct.RemoveSpaces(self.commands[end+1]).startswith("else"):
                return self.GetEndOfBrackets(i)
            return i
        elif ct.RemoveSpaces(self.commands[end+1]).startswith("else"):
            return self.Runner(end+2)
        else:
            return end
    
    def WhileCommand(self, i):
        command = self.commands[i]
        if(not ct.ParentesisEquilized(command)): raise ValueError
        start = i+1
        while(self.expResolver.Calculate(self.GetExpression(self.commands[i])).eval()):
             self.Runner(start)
        return self.GetEndOfBrackets(i)

    def ForCommand(self, i):
        command = self.commands[i]
        self.Attribuition(self.GetExpression(command, True).split(";")[0])
        while(self.expResolver.Calculate(self.GetExpression(command).split(";")[1]).eval()):
            self.Runner(i+1)
            self.instruction(self.GetExpression(command, True).split(";")[2])
        return self.GetEndOfBrackets(i)
        
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
                raise IndentationError
            elif "if" in self.commands[i] or "while" in self.commands[i]:
                brackets_opened += 1
            elif "}" in ct.RemoveSpaces(self.commands[i]): brackets_opened -= 1
            i += 1
        return i-1
    
    def GetExpression(self, command, varless=False):
        if varless:
            return command[command.index('(')+1:-1]
        return self.ReplaceVars(command[command.index('(')+1:-1])
    
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
                
    def CalculateExpression(self, expression):
        root = self.cal.Calculate(expression)
        return int(root.eval())
    
def main():
    prog = Program()
    # prog.Run(sys.argv[1])

if __name__ == "__main__":
    main()