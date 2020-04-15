import configparser


def parseConfig(path):
    config = configparser.ConfigParser()
    # config.sections()
    config.read(path)
    config.sections()
    return config
