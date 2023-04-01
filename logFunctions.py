from colorama import Fore, Back, Style
import colorama
import datetime
import os

colorama.init(convert=True)

bold = '\033[1m'
normal = "\033[0m"

def discordLogger(logRecord):
    message = logRecord.msg
    group = logRecord.name
    levelno = logRecord.levelno
    if len(logRecord.args) > 0: message = message % logRecord.args
    if levelno == 20: logInfo(message, group)
    elif levelno == 30: logWarning(message, group)
    elif levelno == 40: logError(message, group)
    elif levelno == 50: logCritical(message, group)

def logDatetime():
    logTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logTimeString = f"{Fore.LIGHTBLACK_EX}{bold}{logTime}{normal}"
    print(f"{logTimeString}", end=f"{Style.RESET_ALL} ")

def logInfo(message, group, end="\n"):
    logDatetime()
    groupString = f"{normal}{Fore.MAGENTA}{group}{Style.RESET_ALL}"
    print(f"{Fore.BLUE}{Style.BRIGHT}INFO{Style.RESET_ALL}     {groupString} {Style.RESET_ALL}{message}", end=end)

def logWarning(message, group, end="\n"):
    logDatetime()
    groupString = f"{normal}{Fore.MAGENTA}{group}{Style.RESET_ALL}"
    print(f"{Fore.YELLOW}{Style.BRIGHT}WARNING{Style.RESET_ALL}  {groupString} {Style.RESET_ALL}{message}", end=end)

def logError(message, group, end="\n"):
    logDatetime()
    groupString = f"{normal}{Fore.MAGENTA}{group}{Style.RESET_ALL}"
    print(f"{Fore.RED}{Style.BRIGHT}ERROR{Style.RESET_ALL}    {groupString} {Style.RESET_ALL}{message}", end=end)

def logCritical(message, group, end="\n"):
    logDatetime()
    groupString = f"{normal}{Fore.MAGENTA}{group}{Style.RESET_ALL}"
    print(f"{Fore.RED}{Style.BRIGHT}CRITICAL{Style.RESET_ALL}  {groupString} {Style.RESET_ALL}{message}", end=end)

class logHandler():
    def __init__(self, bot): self.bot = bot
    def setFormatter(self): pass
    level = 10
    handle = discordLogger

if __name__ == "__main__":
    logInfo("This is a test", "testGroup")