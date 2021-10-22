def RemoveSpaces(command):
    while(command.startswith(" ")):
        command = command[1:]
    while(command.endswith(" ")):
        command = command[:-1]
    return command

    
def ParentesisEquilized(command):
    i = 0
    for c in command:
        if c == "(": i+=1
        if c == ")": i-=1
    if i == 0: return True
    return False
