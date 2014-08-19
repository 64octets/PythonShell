import os, shlex, sys


homeDirectory = ""
commandHistory = []
commandHistoryEntryNumber = 0
backgroundProcess = False


def setHomeDirectory():
    global homeDirectory
    homeDirectory = os.getcwd()
    return


def inputIsFromFile():
    return not os.isatty(sys.stdin.fileno())


def processInputFromFile():
    for rawInput in sys.stdin:
        print("psh> " + rawInput.rstrip())
        rawInput = rawInput.strip()
        if (len(rawInput) is not 0):
            addToCommandHistory(rawInput)
            processRawInput(rawInput)
    return


def processInputFromKeyboard():
    while (True):
        rawInput = getInput()
        rawInput = rawInput.strip()
        if (len(rawInput) is not 0):
            addToCommandHistory(rawInput)
            processRawInput(rawInput)
    return


def getInput():
    return input("psh> ")


def addToCommandHistory(rawInput):
    global commandHistory
    global commandHistoryEntryNumber
    commandHistoryEntryNumber += 1
    commandHistoryEntry = list()
    commandHistoryEntry.append(str(commandHistoryEntryNumber))
    commandHistoryEntry.append(rawInput)
    if (len(commandHistory) == 10):
        commandHistory.pop(0)
    commandHistory.append(commandHistoryEntry)
    return


def processRawInput(rawInput):
    rawInput = backgroundProcessCheck(rawInput)
    rawCommands = lexicallyAnalyze(rawInput)
    commandSequences = parseRawCommands(rawCommands)
    executeCommands(commandSequences)
    return


def backgroundProcessCheck(rawInput):
    global backgroundProcess
    if (rawInput[len(rawInput) - 1] == "&"):
        rawInput = rawInput[:-1]
        backgroundProcess = True
    else:
        backgroundProcess = False
    return rawInput


def lexicallyAnalyze(rawInput):
    lexicalAnalyzer = shlex.shlex(rawInput, posix=True)
    lexicalAnalyzer.whitespace_split = False
    lexicalAnalyzer.wordchars += "#$+-,./?@^="
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
    if ((len(commandSequences) == 1) and (builtInCommand(commandSequences[0]))):
        handleSingleCommand(commandSequences[0])
    else:
        piping(commandSequences)
    return


def builtInCommand(commandSequence):
    if (commandSequence[0] in ("pwd", "cd", "history", "h")):
        return True
    else:
        return False


def piping(commandSequences):
    if (pipesAreValid(commandSequences)):
        processId = os.fork()
        if (processId == 0):
            executeRecursively(commandSequences)
        else:
            returnId = os.waitpid(processId, 0)
    else:
        print("Invalid use of pipe \"|\"")
    return


def pipesAreValid(commandSequences):
    for command in commandSequences:
        if not command:
            return False
    return True


def executeRecursively(commandSequences):
    if (len(commandSequences) > 1):
        r, w = os.pipe()
        processId = os.fork()
        if (processId == 0):
            setUpChildProcessReadAndWrite(r, w)
            handleSingleCommand(commandSequences[0])
            os.kill(os.getpid(), 1)
        else:
            setUpParentProcessReadAndWrite(r, w)
            os.waitpid(processId, 0)
            commandSequences.pop(0)
            executeRecursively(commandSequences)
    else:
        handleSingleCommand(commandSequences[0])
    return


def handleSingleCommand(commandSequence):
    if (commandSequence[0] == "pwd"):
        executePWD()
    elif (commandSequence[0] == "cd"):
        executeCD(commandSequence)
    elif (commandSequence[0] in ("history", "h")):
        executeHistory(commandSequence)
    else:
        executeShellCommand(commandSequence)
    return


def executePWD():
    print(os.getcwd())
    return


def executeCD(commandSequence):
    try:
        global homeDirectory
        if (len(commandSequence) == 1):
            os.chdir(homeDirectory)
        else:
            os.chdir(commandSequence[1])
    except FileNotFoundError:
        print(commandSequence[0] + ": " + commandSequence[1] + ": No such file or directory")
    return


def executeHistory(commandSequence):
    if (len(commandSequence) == 1):
        executeHistoryWithNoArgs()
    else:
        executeHistoryWithArgs(commandSequence)
    return


def executeHistoryWithNoArgs():
    global commandHistory
    for commandHistoryEntry in commandHistory:
        print(commandHistoryEntry[0] + ": " + commandHistoryEntry[1])
    return


def executeHistoryWithArgs(commandSequence):
    global commandHistory
    commandHistoryTarget = commandSequence[1]
    for commandHistoryEntry in commandHistory:
        if (commandHistoryEntry[0] == commandHistoryTarget):
            commandToBeChanged = commandHistory.pop()
            commandToBeChanged[1] = commandHistoryEntry[1]
            commandHistory.append(commandToBeChanged)
            processRawInput(commandToBeChanged[1])
    return


def executeShellCommand(commandSequence):
    try:
        sys.stdout.flush()
        os.execvp(commandSequence[0], commandSequence)
    except FileNotFoundError:
        print(commandSequence[0] + ": command not found")


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


def main():
    setHomeDirectory()
    if (inputIsFromFile()):
        processInputFromFile()
    else:
        processInputFromKeyboard()


if (__name__ == "__main__"):
    main()
