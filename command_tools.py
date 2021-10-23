from os import truncate


def RemoveSpaces(command):
    while(command.startswith(" ")):
        command = command[1:]
    while(command.endswith(" ")):
        command = command[:-1]
    return command

    
def ParentesisEquilized(command):
    i = 0
    once = False
    for c in command:
        if c == "(": 
            once = True
            i+=1
        if c == ")": i-=1
    if i == 0 and once: return True
    return False
 
def IsBracketlessIf(command):
    i = 0
    while i < len(RemoveSpaces(command)):
        if ParentesisEquilized(command[:i]):
            if not command[i:].isspace():
                return (True, RemoveSpaces(command[i:]))
        i += 1
    return (False, "")

def GetIfExpression(command):
    equalized = 0
    for i in range(command.index("("),len(command)):
        if command[i] == "(":
            equalized += 1
        elif command[i] == ")": 
            equalized -= 1
        elif equalized==0:
            return command[command.index("(")+1:i-1]
    return command