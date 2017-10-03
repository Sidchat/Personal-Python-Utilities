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
import uuid, sys, datetime

class IOWrapper:
    """This class is main class in the file. It defines variables and functions to achieve objectives in docstring"""
    def __init__(self, logfilename='', outputtarget='SCREEN', loglevel='INFO'):
        self.Targets = list(map(lambda arg: arg.upper().replace(' ',''), outputtarget.split(',')))
        self.writeToConsole = True if 'SCREEN' in self.Targets else False
        self.writeToLog = True if 'LOG' in self.Targets else False
        if self.writeToLog == True:
            self.logFileName= str(uuid.uuid1()) if logfilename != '' else logfilename
        self.logMessageCount = 0
        self.dictLogLevel={'LOG-INTERNAL':0, 'INFO':1, 'WARNING':2, 'ERROR': 3, 'CRITICAL':5}
        self.logLevel = self.dictLogLevel.get(loglevel,0)
        self.logOpened = False
        self.logHandler = None
        self.lastStatus= "Class IOWrapper is instantiated." if len(self.Targets) > 0 else 'No valid target modes provided'
    def getlogfilename(self):
        return self.logFileName
    def getlaststatusmessage(self):
        return self.lastStatus
    def setlogfilename(self, logfilename=''):
        if logfilename == '':
            self.lastStatus = 'No log file was provided.'
            return False
        self.writeToLog = True
        self.logFileName = logfilename
        self.logMessageCount = 0
        return True
    def setloglevel(self, loglevel):
        self.logLevel = self.dictLogLevel.get(loglevel,0)
    def write(self, message, loglevel='INFO',lastmessage=False):
        if self.writetoscreen(message, loglevel.upper().replace(' ','')) if self.writeToConsole else True & \
        self.writetologfile(message, loglevel.upper().replace(' ','')) if self.writeToLog else True:
            if lastmessage & self.writeToLog:
                self.closelog()
            return
        else:
            raise Exception(f"Output failed for some reason. Status of last operation:{self.lastStatus}")
    def writetoscreen(self,message, loglevel):
        if self.dictLogLevel.get(loglevel,0) < self.logLevel:
            self.lastStatus = f'Current Log level is {self.logLevel}, requested log level is {loglevel}'
            return True
        print(f"{datetime.datetime.now().isoformat(timespec='seconds')}:<{loglevel}>:{message}")
        self.logMessageCount = self.logMessageCount + 1
        return True
    def openlogfile(self):
        if self.logOpened:
            return True
        if self.logFileName == '':
            raise  Exception('No log file is provided')
        try:
            self.logHandler = open(self.logFileName, 'a')
        except:
            raise Exception(f"Can not open log file. Here is error: {sys.exc_info()[0]}")
        self.logOpened = True
        return True
    def closelog(self):
        self.logHandler.close()
    def writetologfile(self,message,loglevel):
        if self.dictLogLevel.get(loglevel,0) < self.logLevel:
            self.lastStatus = f'Current Log level is {self.logLevel}, requested log level is {loglevel}'
            return True
        if self.openlogfile:
            self.logHandler.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}:<{loglevel}>:{message}")
            self.logMessageCount = self.logMessageCount + 1
            return True
        return False


if __name__ == "__main__":
    io = IOWrapper()
    io.write("Message Starts.")
    io.write("Message Ends.", lastmessage=True)