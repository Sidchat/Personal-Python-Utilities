#!/usr/bin/env python3
""" This program creates a class that users can use to wrap around input-ouput system that offers to perform
               1) Writing to log file or screen
               2) Filtering different levels of messages
               3) Automatic log management
               4) Input prompt display and logging
               5) Input validation against a list"""
__author__ = "Siddhartha Chatterjee"
__license__ = "GPL"
__version__ = "0.1"
import uuid, sys, datetime, os, io, shutil, os.path
import glob, math, platform, configparser


class IOWrapper:
    """This class is main class in the file. It defines variables and functions to achieve objectives in docstring"""

    def __init__(self, logfilename: str = '', outputtarget: str = 'SCREEN', loglevel: str = 'INFO', commitcount: int = 100,
                 protectdisk: bool =True, rotatelog: bool=False, rotateloglimit:str='1MB', rotatelogcount:int=10) -> object:
        self.Targets: list = list(map(lambda arg: arg.upper().replace(' ', ''), outputtarget.split(',')))
        self.writeToConsole: bool = True if 'SCREEN' in self.Targets else False
        self.writeToLog: bool = True if 'LOG' in self.Targets else False
        if self.writeToLog == True:
            self.logFileName: str = str(uuid.uuid1()) if logfilename == '' else logfilename
            self.logFileDirectory: str = '.' if os.path.dirname(self.logFileName) == '' else os.path.dirname(self.logFileName)
            self.logConfigFile: str = os.path.join(self.logFileDirectory,'.iowrapper.config')
            self.protectDiskOnWrite = protectdisk
        self.logMessageCount: int = 0
        self.dictLogLevel: dict = {'VERBOSE': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 5, 'LOG-INTERNAL':6}
        if loglevel == 'LOG-INTERNAL':
            loglevel = 'CRITICAL'
        self.logLevel: int = self.dictLogLevel.get(loglevel, 0)
        self.logOpened: bool = False
        self.logHandler: typing.io = None
        self.logFileCommitCount: int = commitcount
        self.logFileSize: int = 0
        self.rotateLog: bool = rotatelog if self.writeToLog else False
        if rotatelogcount > 999:
            raise Exception(f"Can not have more than 999 rotating logs.")
        self.rotateLogCount: int = rotatelogcount
        if rotateloglimit.endswith('MB'):
            self.rotateLogSizeInKB: float = float(rotateloglimit.replace('MB','')) * 1024
        else:
            if rotateloglimit.endswith('KB'):
                self.rotateLogSizeInKB: float = float(rotateloglimit.replace('KB',''))
            else:
                self.rotateLogSizeInKB: float = float(rotateloglimit) / 1024
        self.latestLogCount: int = 0
        self.newLogFileName: str = ''
        self.ioConfig: configparser.ConfigParser = None
        if rotatelog:
            self.setConfig()
        self.freeDiskSpaceLimit: int = 10 #10MB in total in current drive
        self.lastStatus: str = f"Class IOWrapper is instantiated. Output set to {self.writeToLog}" if len(
            self.Targets) > 0 else 'No valid target modes provided'

    def getlogfilename(self) -> str:
        return self.logFileName

    def getfreediskspace(self) -> float:
        try:
            total, used, free = shutil.disk_usage(self.logFileDirectory)
        except:
            raise Exception(
                f"Log output: {self.writeToLog}.\nLog File: {self.logFileName}\nStatus of last operation:{self.lastStatus}")
        return free / (1024*1024)

    def getlaststatusmessage(self) -> str:
        return self.lastStatus

    def readFromKeyBoard(self, prompt: str="Please supply a value: ") -> str:
        userInput = input(f"{prompt}[Type 'HELP' without quote to see a list of choices or type QUIT to exit] : ").strip('\n')
        return userInput

    def getInputAndValidate(self, prompt: str, validate: list = [0], yesno: bool = False, parsenumber: bool = False, rangecheck: list = [0]) -> str:
        if len(validate) == 1 and validate[0] == 0:
            validate.pop()
        if yesno and not validate:
            validate = ['yes','y','Y','YES','Yes','NO','No','no','n','N']
        userValue = self.readFromKeyBoard(prompt)
        if userValue.upper() == "QUIT":
            raise Exception("ERROR: User aborted the operation.")
        if userValue.upper() == "HELP":
            print("=" * 25)
            if validate:
                print(f"Acceptable values are: {'/'.join(validate)}")
            else:
                print("ERROR: No choices are given.")
            print("=" * 25)
            userValue = self.getInputAndValidate(prompt, validate, yesno, parsenumber, rangecheck=rangecheck)
        if parsenumber:
            try:
                anynumber: float = float(userValue)
            except ValueError:
                print("ERROR: The input value is not numeric. Please provide the input value.\n")
                return self.getInputAndValidate(prompt, validate, parsenumber=True, rangecheck=rangecheck)
            if len(rangecheck) == 2:
                if anynumber >= rangecheck[0] and anynumber <= rangecheck[1]:
                    return userValue
                else:
                    print(f"ERROR: The entered numeric value is not within ({rangecheck[0]}, {rangecheck[1]}).")
                    return self.getInputAndValidate(prompt, validate, parsenumber=True, rangecheck=rangecheck)
        if not validate:
            if self.writetologfile(f"{prompt} : {userValue}", "INFO"):
                return userValue
        if userValue in validate or userValue.upper() in validate:
            if self.writetologfile(f"{prompt} : {userValue}; User input is checked.", "INFO"):
                return userValue
        else:
            print("ERROR: The entered value is not among given choices.")
            return self.getInputAndValidate(prompt, validate, yesno, parsenumber, rangecheck)

    def setConfig(self):
        self.ioConfig = configparser.ConfigParser()
        defaultLogConfig = {'Log Rotation':'Yes', 'Maximum Log Files':f"{self.rotateLogCount}",
                            'Maximum Log Size':f"{self.rotateLogSizeInKB}KB", 'Current Log Counter':'0'}
        if os.path.exists(self.logConfigFile):
            self.ioConfig.read(self.logConfigFile)
        else:
            self.ioConfig.read_dict({'Log Configuration': defaultLogConfig})
            self.saveConfig()

    def saveConfig(self):
        with open(self.logConfigFile,'w') as conf:
            self.ioConfig.write(conf)

    def updateLogCounterConfigValue(self, logCounter: int):
        self.ioConfig['Log Configuration']['Current Log Counter'] = str(logCounter)
        self.saveConfig()

    def setlogfilename(self, logfilename: str='') -> bool:
        if logfilename == '':
            self.lastStatus = 'No log file was provided.'
            return False
        self.writeToLog = True
        self.logFileName = logfilename
        self.logFileDirectory = '.' if os.path.dirname(self.logFileName) == '' else os.path.dirname(self.logFileName)
        self.logMessageCount = 0
        return True

    def setloglevel(self, loglevel: str):
        if loglevel == 'LOG-INTERNAL':
            loglevel = 'CRITICAL'
        self.logLevel = self.dictLogLevel.get(loglevel, 0)

    def write(self, message: str, loglevel: str ='INFO', lastmessage: bool =False):
        writtentolog: bool = self.writetologfile(message, loglevel.upper().replace(' ', '')) if self.writeToLog else True
        writtentoscreen: bool = self.writetoscreen(message,
                                             loglevel.upper().replace(' ', '')) if self.writeToConsole else True
        if writtentoscreen and writtentolog:
            self.logMessageCount = self.logMessageCount + 1
            if self.logMessageCount > self.logFileCommitCount:
                self.lastStatus = f"Flushing log {self.logFileName} to disk."
                self.logHandler.flush()
                os.fsync(self.logHandler.fileno())
                self.logMessageCount = 0
            if lastmessage & self.writeToLog:
                self.closelog()
            return True
        else:
            raise Exception(
                f"Output failed for some reason. Screen output: {writtentoscreen}, log output: {writtentolog}.\n Status of last operation:{self.lastStatus}")

    def writetoscreen(self, message: str, loglevel: str) -> bool:
        if self.dictLogLevel.get(loglevel, 0) < self.logLevel:
            self.lastStatus = f'Current Log level is {self.logLevel}, requested log level is {loglevel}'
            return True
        print(f"{datetime.datetime.now().isoformat(timespec='seconds')}:<{loglevel}>:{message}")
        return True

    def openlogfile(self):
        if self.logOpened:
            return True
        if self.logFileName == '':
            raise Exception('No log file is provided')
        try:
            self.logHandler = open(self.logFileName, 'a')
        except:
            raise Exception(f"Can not open log file. Here is error: {sys.exc_info()[0]}")
        self.logOpened = True
        self.logFileSize = os.path.getsize(self.logFileName)
        return True

    def closelog(self, errorcondition=False):
        if self.logOpened:
            if errorcondition == False:
                self.lastStatus = f"Log file {self.logFileName} is closed. "
            self.logHandler.close()
            self.logFileSize = 0
            self.logOpened = False

    def closecurrentlog(self, fillupspacecount: float=0):
        filler: str = ' '
        if fillupspacecount > 0:
            fillCount: int = 1 if math.floor(fillupspacecount) == 0 else math.floor(fillupspacecount)
            self.logHandler.write(filler * fillCount)
        self.closelog()
        return True

    def renamelog(self):
        logExtension: str = os.path.basename(self.logFileName).split('.')[-1]
        logName: str = '.'.join(os.path.basename(self.logFileName).split('.')[:-1])
        # It looked like some platforms like Windows do not report modified filestamps reliably enough
        # to find the most recently updated log file based on timestamp. Therefore log configuration file is
        # designed to store the log counters. If log file name is changed or rotation parameters are altered
        # please delete the configuration file from log directory. Also, the design of log configuration file
        # prevents the developer to use two different log files with their own rotation schemes in the same directory.
        # Use necessary precaution like changing log directory or delete older log files to prevent unpredictable
        # behavior.
        self.latestLogCount = int(self.ioConfig['Log Configuration']['Current Log Counter'])
        newcount: int = (self.latestLogCount+1) % (self.rotateLogCount+1)
        self.newLogFileName = os.path.join(self.logFileDirectory, f"{logName}.{1 if newcount == 0 else newcount:03}.{logExtension}")
        try:
            shutil.move(self.logFileName, self.newLogFileName)
        except:
            raise Exception(f"Could not rename log {self.logFileName} to {self.newLogFileName}. Error - {sys.exc_info()[0]}")
        self.updateLogCounterConfigValue(1 if newcount == 0 else newcount)
        return True

    def writetologfile(self, message: str, loglevel: str) -> bool:
        if not self.writeToLog:
            return True
        if self.dictLogLevel.get(loglevel, 0) < self.logLevel:
            self.lastStatus = f'Current Log level is {self.logLevel}, requested log level is {loglevel}'
            return True
        if not self.logOpened:
            if self.openlogfile():
                self.lastStatus = f"Log file {self.logFileName} is opened for writing."
        # If the platform is windows, need to add 1 byte for each newline character while writing to log file
        crlfByte: int = 1 if platform.system() == 'Windows' else 0
        newMessage: str = f"{datetime.datetime.now().isoformat(timespec='seconds')}:<{loglevel}>:{message}\n"
        extraCrlfBytes: int = crlfByte * int(newMessage.count('\n'))
        self.logFileSize = (self.logFileSize + len(newMessage)+extraCrlfBytes)
        # Protect disk by measuring to see if you are running out of disk space
        if (self.getfreediskspace() - (
            self.logFileSize / (1024 * 1024)) < self.freeDiskSpaceLimit) and self.protectDiskOnWrite == True:
            self.lastStatus = f'Running out of free disk space. Free space is less than {self.freeDiskSpaceLimit}.'
            self.logHandler.write(self.lastStatus)
            self.closelog(True)
            return False
        #If rotate logging is on
        if self.rotateLog:
            # Check if logFileSize is over the limit
            if self.logFileSize > (self.rotateLogSizeInKB * 1024 ):
                if self.closecurrentlog((self.rotateLogSizeInKB * 1024 ) -
                                                (self.logFileSize - len(newMessage) - extraCrlfBytes)) and self.renamelog():
                    if self.openlogfile():
                        self.lastStatus = f"Log file is rotated because size limit of {self.rotateLogSizeInKB}KB is reached. Latest log counter is {self.latestLogCount+1}."
                        oldlogreminder: str = f"{datetime.datetime.now().isoformat(timespec='seconds')}:<LOG-INTERNAL>:Older log entries are in {self.newLogFileName}\n"
                        oldlogreminderlen: int = len(oldlogreminder)+crlfByte
                        if oldlogreminderlen + len(newMessage) < (self.rotateLogSizeInKB * 1024 ):
                            self.logHandler.write(oldlogreminder)
                            self.logFileSize = self.logFileSize + oldlogreminderlen
                        self.logFileSize = self.logFileSize + len(newMessage)+extraCrlfBytes
        self.logHandler.write(newMessage)
        return True


if __name__ == "__main__":
    io = IOWrapper(logfilename="example.log", outputtarget="SCREEN,LOG", rotatelog=True,rotateloglimit='1KB',rotatelogcount=10)
    io.write("Message Starts.")
    for i  in range(1,5):
        io.write(f"Message number {i} is written here.")
    io.write("Message Ends.")
    print(io.getInputAndValidate("Enter some string", parsenumber=True, rangecheck=[1,100]))
    print(io.getlaststatusmessage())
