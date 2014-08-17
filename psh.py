import os

def getInput():
    return input("psh> ")

def main():
    while(True):
        rawInput = getInput()
        print(rawInput)
        os.execvp("ls", ["ls", "-l"])

if (__name__ == "__main__"):
    main()
