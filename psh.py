import os, shlex

def getInput():
    return input("psh> ")

def parseRawInput(rawInput):
    lexicalAnalyzer = shlex.shlex(rawInput, posix=True)
    lexicalAnalyzer.whitespace_split = False
    lexicalAnalyzer.wordchars += '#$+-,./?@^='
    return list(lexicalAnalyzer)

def parseRawCommands(commands):
    pipeIndexes = []
    currentIndex = 0
    for command in commands:
        if (command == '|'):
            pipeIndexes.append(currentIndex)
        currentIndex += 1
    commandSequences = splitOnPipeIndexes(pipeIndexes, commands)
    return commandSequences

def splitOnPipeIndexes(pipeIndexes, commands):
    commandSequences = []
    previousPipeIndex = 0
    for pipeIndex in pipeIndexes:
        commandSequence = commands[previousPipeIndex:pipeIndex]
        commandSequences.append(commandSequence)
        previousPipeIndex = pipeIndex + 1
    commandSequences.append(commands[previousPipeIndex:])
    return commandSequences

def executeCommands(commandSequences):
    if (not pipesAreValid(commandSequences)):
        return
    processId = os.fork()
    if (processId == 0):
        executeRecursively(commandSequences)
    else:
        returnId = os.waitpid(processId, 0)
    return

def pipesAreValid(commandSequences):
    if (len(commandSequences) > 1):
        for command in commandSequences:
            if not command:
                print("Invalid use of pipe \"|\"")
                return False
    return True

def executeRecursively(commandSequences):
    if (len(commandSequences) == 1):
        executeSingleCommand(commandSequences[0])
        return
    else:
        r, w = os.pipe()
        processId = os.fork()
        if (processId == 0):
            setUpChildProcessReadAndWrite(r, w)
            executeSingleCommand(commandSequences[0])
        else:
            setUpParentProcessReadAndWrite(r, w)
            os.waitpid(processId, 0)
            commandSequences.pop(0)
            executeSingleCommand(commandSequences[0])

def setUpChildProcessReadAndWrite(r, w):
    os.close(1)
    os.dup2(w, 1)
    os.close(r)
    os.close(w)
    return

def setUpParentProcessReadAndWrite(r, w):
    os.close(0)
    os.dup2(r, 0)
    os.close(r)
    os.close(w)
    return

def executeSingleCommand(command):
    if (command[0] == "pwd"):
        executePWD()
    elif(command[0] == "cd"):
        executeCD(command)
    return

def executePWD():
    print(os.getcwd())
    return

def executeCD(command):
    try:
        if (len(command) == 1):
            os.chdir(os.getenv("HOME"))
        else:
            os.chdir(command[1])
    except FileNotFoundError:
        print(command[0] + ": " + command[1] + ": No such file or directory")
    return

def executeShellCommand(command):
    try:
        os.execvp(command[0], command)
    except FileNotFoundError:
        print(command[0] + ": command not found")
    return

def main():
    while (True):
        rawInput = getInput()
        rawCommands = parseRawInput(rawInput)
        commandSequences = parseRawCommands(rawCommands)
        executeCommands(commandSequences)

if (__name__ == "__main__"):
    main()
