#!/usr/bin/env python

import os
import sys
import logging
import dbus
import _thread as thread

from config import ChargerConfig

# add the path to our own packages for import
sys.path.insert(1, "/data/SetupHelper/velib_python")

from vedbus import VeDbusService, VeDbusItemImport
from vreg_link_item import VregLinkItem, GenericReg, ChargerReg

from gi.repository import GLib


class ChargerMeterService:

    def __init__(self, servicename, deviceinstance, paths, connection='USB', config=None):
        self.config = config or ChargerConfig()
        self._dbusservice = VeDbusService(servicename, register=False)
        self._paths = paths
        self.device = self.config.get_device()

        product_name = self.config.get_product_name()

        vregtype = lambda *args, **kwargs: VregLinkItem(*args, **kwargs,
                                                        getvreg=self.vreg_link_get, setvreg=self.vreg_link_set)

        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', self.config.get_version())
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        # value used in ac_sensor_bridge.cpp of dbus-cgwacs
        self._dbusservice.add_path('/ProductId', 0xA389)
        self._dbusservice.add_path('/ProductName', product_name)
        self._dbusservice.add_path('/DeviceName', product_name)
        self._dbusservice.add_path('/FirmwareVersion', 0x0416)
        self._dbusservice.add_path('/Connected', 1)
        self._dbusservice.add_path('/Serial', "HQ2084P4XX")

        self._dbusservice.add_path('/Devices/0/CustomName', product_name)
        self._dbusservice.add_path('/Devices/0/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/Devices/0/FirmwareVersion', 0x0416)
        self._dbusservice.add_path('/Devices/0/ProductId', 0xA389)
        self._dbusservice.add_path('/Devices/0/ProductName', "SmartShunt 300A/50mV")
        self._dbusservice.add_path('/Devices/0/ServiceName', servicename)
        self._dbusservice.add_path('/Devices/0/Serial', "HQ2084P4XX")
        self._dbusservice.add_path('/Devices/0/VregLink', None, itemtype=vregtype)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, settings['initial'], writeable=True, onchangecallback=self._handle_changed_value)

        self._dbusservice.register()
        GLib.timeout_add(1000, self._update)

    def _update(self):
        try:
            dbus_conn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

            has_charger = self.device in dbus_conn.list_names()

            if has_charger:
                self._dbusservice['/Connected'] = 1
                self._dbusservice['/Mode'] = 1
                current = VeDbusItemImport(dbus_conn, self.device, '/Dc/0/Current')
                voltage = VeDbusItemImport(dbus_conn, self.device, '/Dc/0/Voltage')
                state = VeDbusItemImport(dbus_conn, self.device, '/State')
                temperature = VeDbusItemImport(dbus_conn, self.device, '/Dc/0/Temperature')

                if current is not None and current.get_value() is not None:
                    self._dbusservice['/Dc/0/Voltage'] = voltage.get_value()
                    self._dbusservice['/Dc/0/Current'] = current.get_value()
                    self._dbusservice['/Dc/0/Power'] = current.get_value() * voltage.get_value()
                    self._dbusservice['/Dc/0/Temperature'] = temperature.get_value()
                    self._dbusservice['/State'] = state.get_value()
                else:
                    self.set_disconnected()
            else:
                for d in dbus_conn.list_names():
                    if d.startswith('com.victronenergy.charger.ttyUSB'):
                        self.device = d
                        break;
                self.set_disconnected()
        except Exception:
            logging.exception("Failed to update charger meter")

        index = self._dbusservice['/UpdateIndex'] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
            self._dbusservice['/UpdateIndex'] = index
            return True

        return True

    def set_disconnected(self):
        self._dbusservice['/Connected'] = 0
        self._dbusservice['/State'] = 0
        self._dbusservice['/Mode'] = 4
        self._dbusservice['/Dc/0/Voltage'] = None
        self._dbusservice['/Dc/0/Current'] = None
        self._dbusservice['/Dc/0/Power'] = None
        self._dbusservice['/Dc/0/Temperature'] = None

    @staticmethod
    def _handle_changed_value(self, path, value):
        return True

    @staticmethod
    def vreg_link_get(reg_id):
        if reg_id == ChargerReg.DC_MONITOR_MODE:
            return GenericReg.OK.value, [0xFE]
        return GenericReg.OK.value, []

    @staticmethod
    def vreg_link_set(reg_id, data):
        return GenericReg.OK.value, data


def main():
    config = ChargerConfig()

    # set logging level to include info level entries
    level = logging.INFO
    if config.get_debug():
        level = logging.DEBUG
    logging.basicConfig(level=level)

    logging.basicConfig(level=level)
    logging.info(">>>>>>>>>>>>>>>> DC Source Starting <<<<<<<<<<<<<<<<")

    thread.daemon = True  # allow the program to quit

    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    service = ChargerMeterService(
        servicename='com.victronenergy.dcsource.ip22',
        deviceinstance=293,
        paths={

            '/State': {'initial': 0},
            '/Mode': {'initial': 4},

            '/Dc/0/Voltage': {'initial': None},  # OK
            '/Dc/0/Current': {'initial': None},
            '/Dc/0/Temperature': {'initial': None},
            '/Dc/0/Power': {'initial': None},
            '/History/EnergyOut': {'initial': None},

            '/Settings/DeviceFunction': {'initial': 0},
            '/Settings/MonitorMode': {'initial': -2},
            '/ChargeCurrentLimit': {'initial': 15},

            '/UpdateIndex': {'initial': 0}
        },
        config=config
    )

    logging.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
