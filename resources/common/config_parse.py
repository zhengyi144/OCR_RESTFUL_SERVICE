import os
from dotenv import load_dotenv
from .tools import loadJsonFile

load_dotenv(verbose=True)

class ConfigParser:
    def __init__(self,configPath="config/config.json"):
        self.env=os.getenv("ENV")
        self.configPath=configPath
        self.loadConfigData()
    
    def loadConfigData(self):
        fileData=loadJsonFile(self.configPath)
        if self.env=="dev":
            envData=fileData["dev"]
        elif self.env=="pro":
            envData=fileData["pro"]
        self.mysql = envData["mysql"]
        self.filePath=envData["filePath"]
        self.serverHost=envData["serverHost"]


if __name__=="__main__":
    config=ConfigParser("dev")
    print(config.mysql)