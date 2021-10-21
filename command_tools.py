def RemoveSpaces(command):
    while(command.startswith(" ")):
        command = command[1:]
    while(command.endswith(" ")):
        command = command[:-1]
    return command