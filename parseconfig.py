import configparser

def parseConfig(path):
  config = configparser.ConfigParser()
  config.read(path)
  return config
