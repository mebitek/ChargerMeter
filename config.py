import configparser
import os
import shutil


class ChargerConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        config_file = "%s/../conf/charger_meter_config.ini" % (os.path.dirname(os.path.realpath(__file__)))
        if not os.path.exists(config_file):
            sample_config_file = "%s/config.sample.ini" % (os.path.dirname(os.path.realpath(__file__)))
            shutil.copy(sample_config_file, config_file)
        self.config.read("%s/../conf/charger_meter_config.ini" % (os.path.dirname(os.path.realpath(__file__))))

    def get_device(self):
        return self.config.get('Setup', 'device', fallback="om.victronenergy.charger.ttyUSB0")

    def get_debug(self):
        val = self.config.get("Setup", "debug", fallback=False)
        if val == "true":
            return True
        else:
            return False

    def get_product_name(self):
        return self.config.get("Setup", "name", fallback="Virtual AC Charger Meter")

    @staticmethod
    def get_version():
        with open("%s/version" % (os.path.dirname(os.path.realpath(__file__))), 'r') as file:
            return file.read()