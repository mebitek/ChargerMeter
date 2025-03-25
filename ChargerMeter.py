#!/usr/bin/env python

import os
import sys
import json
import logging
import dbus
import requests
import _thread as thread

from config import ChargerConfig

# add the path to our own packages for import
sys.path.insert(1, "/data/SetupHelper/velib_python")

from vedbus import VeDbusService, VeDbusItemImport
from vreg_link_item import VregLinkItem, GenericReg

from gi.repository import GLib


class ChargerMeterService:

    def __init__(self, servicename, deviceinstance, paths, productname='Virtual AC Charger Meter', connection='MQTT',
                 config=None):
        self.config = config or ChargerConfig()
        self._dbusservice = VeDbusService(servicename, register=False)
        self._paths = paths

        vregtype = lambda *args, **kwargs: VregLinkItem(*args, **kwargs,
                                                        getvreg=self.vreglink_get, setvreg=self.vreglink_set)

        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', "v0.1")
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        # value used in ac_sensor_bridge.cpp of dbus-cgwacs
        self._dbusservice.add_path('/ProductId', 0xA389)
        self._dbusservice.add_path('/ProductName', productname)
        self._dbusservice.add_path('/DeviceName', productname)
        self._dbusservice.add_path('/FirmwareVersion', 0x0416)
        self._dbusservice.add_path('/Connected', 1)
        self._dbusservice.add_path('/Serial', "HQ2084P4XX")

        self._dbusservice.add_path('/Devices/0/CustomName', productname)
        self._dbusservice.add_path('/Devices/0/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/Devices/0/FirmwareVersion', 0x0416)
        self._dbusservice.add_path('/Devices/0/ProductId', 0xA389)
        self._dbusservice.add_path('/Devices/0/ProductName', "Virtual AC Energy Meter")
        self._dbusservice.add_path('/Devices/0/ServiceName', servicename)
        self._dbusservice.add_path('/Devices/0/Serial', "HQ2084P4XX")
        self._dbusservice.add_path('/Devices/0/VregLink', None, itemtype=vregtype)

        for path, settings in self._paths.items():
                self._dbusservice.add_path(
                    path, settings['initial'], writeable=True, onchangecallback=self._handlechangedvalue)

        self._dbusservice.register()
        GLib.timeout_add(1000, self._update)

    def _update(self):

        dbus_conn = dbus.SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else dbus.SystemBus()

        device = self.config.get_device()
        has_charger = device in dbus_conn.list_names()

        if has_charger:
            current = VeDbusItemImport(dbus_conn, device, '/Dc/0/Current')
            voltage = VeDbusItemImport(dbus_conn, device, '/Dc/0/Voltage')
            state = VeDbusItemImport(dbus_conn, device, '/State')
            temperature = VeDbusItemImport(dbus_conn, device, '/Dc/0/Temperature')

            if current is not None and current.get_value() is not None:
                self._dbusservice['/Dc/0/Voltage'] = voltage.get_value()
                self._dbusservice['/Dc/0/Current'] = -current.get_value()
                self._dbusservice['/Dc/0/Power'] = current.get_value() * voltage.get_value()
                self._dbusservice['/Dc/0/Temperature'] = temperature.get_value()
                self._dbusservice['/State'] = state.get_value()
            else:
                self.set_disconnected()
        else:
            self.set_disconnected()

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


    def _handlechangedvalue(self, path, value):
        return True

    def vreglink_get(self, regid):
        if regid == 0xEEB8:
            logging.info("vreglink_get %s" % regid)
            return GenericReg.OK.value, [0xFE]
        return GenericReg.OK.value, []

    def vreglink_set(self, regid, data):
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

    pvac_output = ChargerMeterService(
        servicename='com.victronenergy.dcsource.ip22',
        deviceinstance=291,
        paths={

            '/State': {'initial': 3},
            '/Mode': {'initial': 1},

            '/Dc/0/Voltage': {'initial': 12.8}, #OK
            '/Dc/0/Current': {'initial': 14.8},
            '/Dc/0/Temperature': {'initial': 18},
            '/Dc/0/Power': {'initial': 189},
            #'/History/EnergyOut': {'initial': 10},


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