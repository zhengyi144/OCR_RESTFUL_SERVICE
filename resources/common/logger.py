import os
import sys
import logging
import functools
from concurrent_log_handler import ConcurrentRotatingFileHandler
#from logging.handlers import TimedRotatingFileHandler

logger_initialized = {}

@functools.lru_cache()
def get_logger(name="main",log_file=None,log_level=logging.INFO,maxBytes=10*1024*1024,backupCount=5):
    logger = logging.getLogger(name)
    if name in logger_initialized:
        return logger
    for logger_name in logger_initialized:
        if name.startswith(logger_name):
            return logger

    formatter = logging.Formatter(
        '[%(asctime)s] %(name)s %(levelname)s: %(message)s',
        datefmt="%Y/%m/%d %H:%M:%S")

    #stream_handler = logging.StreamHandler(stream=sys.stdout)
    #stream_handler.setFormatter(formatter)
    #logger.addHandler(stream_handler)
    if log_file is not None:
        log_file_folder = os.path.split(log_file)
        os.makedirs(log_file_folder[0], exist_ok=True)
        #file_handler = logging.FileHandler(log_file, 'a')
        #file_handler=TimedRotatingFileHandler(filename=log_file,when=when,backupCount=3,interval=interval)
        file_handler=ConcurrentRotatingFileHandler(log_file,mode='a',maxBytes=maxBytes,backupCount=backupCount)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.setLevel(log_level)
    logger_initialized[name] = True
    return logger


if __name__=="__main__":
    logger=get_logger("log",log_file="logs/logger.log")
    logger.info("test info logger!")
    logger.error("test error logger!")


