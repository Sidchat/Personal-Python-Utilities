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
import glob, math


class IOWrapper:
    """This class is main class in the file. It defines variables and functions to achieve objectives in docstring"""

    def __init__(self, logfilename: str = '', outputtarget: str = 'SCREEN', loglevel: str = 'INFO', commitcount: int = 100,
                 protectdisk: bool =True, rotatelog: bool=False, rotateloglimit:str='1MB', rotatelogcount:int=10) -> object:
        self.Targets: list = list(map(lambda arg: arg.upper().replace(' ', ''), outputtarget.split(',')))
        self.writeToConsole: bool = True if 'SCREEN' in self.Targets else False
        self.writeToLog: bool = True if 'LOG' in self.Targets else False
        if self.writeToLog == True:
            self.logFileName: str = str(uuid.uuid1()) if logfilename == '' else logfilename
            self.logFileDirectory: str = '.' if os.path.dirname(self.logFileName) == '' else os.path.dirname(
                self.logFileName)
            self.protectDiskOnWrite = protectdisk
        self.logMessageCount: int = 0
        self.dictLogLevel: dict = {'LOG-INTERNAL': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 5}
        self.logLevel: int = self.dictLogLevel.get(loglevel, 0)
        self.logOpened: bool = False
        self.logHandler: typing.io = None
        self.logFileCommitCount: int = commitcount
        self.logFileSize: int = 0
        self.rotateLog: bool = rotatelog
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
        fillCount: int = 1 if math.floor(fillupspacecount) == 0 else math.floor(fillupspacecount)
        self.logHandler.write(filler * fillCount)
        self.closelog()
        return True

    def renamelog(self):
        logExtension: str = os.path.basename(self.logFileName).split('.')[-1]
        logName: str = '.'.join(os.path.basename(self.logFileName).split('.')[:-1])
        latestLogFile: str = max(glob.glob(os.path.join(self.logFileDirectory,f'{logName}.*.{logExtension}')),key=os.path.getctime)
        self.latestLogCount = int(os.path.basename(latestLogFile).split('.')[-2])
        self.newLogFileName = os.path.join(self.logFileDirectory, f"{logName}.{(self.latestLogCount+1) % self.rotateLogCount}.{logExtension}")
        try:
            shutil.move(self.logFileName, self.newLogFileName)
        except:
            raise Exception(f"Could not rename log {self.logFileName} to {self.newLogFileName}. Error - {sys.exc_info()[0]}")
        return True

    def writetologfile(self, message: str, loglevel: str) -> bool:
        if self.dictLogLevel.get(loglevel, 0) < self.logLevel:
            self.lastStatus = f'Current Log level is {self.logLevel}, requested log level is {loglevel}'
            return True
        if not self.logOpened:
            if self.openlogfile():
                self.lastStatus = f"Log file {self.logFileName} is opened for writing."
        newMessage: str = f"{datetime.datetime.now().isoformat(timespec='seconds')}:<{loglevel}>:{message}\n"
        self.logFileSize = (self.logFileSize + len(newMessage))
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
                if self.closecurrentlog((self.rotateLogSizeInKB * 1024 ) - \
                                                (self.logFileSize - len(newMessage))) and self.renamelog():
                    if self.openlogfile():
                        self.lastStatus = f"Log file is rotated because size limit of {self.rotateLogSizeInKB} is reached. Latest log counter is {self.latestLogCount}."
                        self.logHandler.write(f"Older log entries are in {self.newLogFileName}.")
        self.logHandler.write(newMessage)
        return True


if __name__ == "__main__":
    io = IOWrapper(logfilename="example.log", outputtarget="SCREEN,LOG", rotatelog=True,rotateloglimit='3KB',rotatelogcount=10)
    io.write("Message Starts.")
    for i  in range(1,200):
        io.write(f"Message number {i} is written here.")
    io.write("Message Ends.")
    print(io.getlaststatusmessage())
