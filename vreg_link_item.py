from enum import Enum

from vedbus import VeDbusItemExport
import dbus

class VregLinkItem(VeDbusItemExport):
    def __init__(self, *args, getvreg=None, setvreg=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.getvreg = getvreg
        self.setvreg = setvreg

    @dbus.service.method('com.victronenergy.VregLink',
                         in_signature='q', out_signature='qay')
    def GetVreg(self, regid):
        return self.getvreg(int(regid))

    @dbus.service.method('com.victronenergy.VregLink',
                         in_signature='qay', out_signature='qay')
    def SetVreg(self, regid, data):
        return self.setvreg(int(regid), bytes(data))

class GenericReg(Enum):
    OK=0x0000

class InverterReg(Enum):
    VE_REG_DEVICE_MODE=0x0200
    VE_REG_INV_WAVE_SET50HZ_NOT60HZ=0xEB03
    VE_REG_AC_OUT_VOLTAGE = 0x2200
    VE_REG_AC_OUT_CURRENT = 0x2201
    VE_REG_DC_CHANNEL1_VOLTAGE = 0xED8D
    VE_REG_AC_OUTPUT_L1_APPARENT_POWER = 0x2216
    VE_REG_AC_OUT_APPARENT_POWER = 0x2205
    VE_REG_SHUTDOWN_LOW_VOLTAGE_SET = 0x2210
    VE_REG_ALARM_LOW_VOLTAGE_SET = 0x0320
    VE_REG_ALARM_LOW_VOLTAGE_CLEAR = 0x0321
    VE_REG_INV_PROT_UBAT_DYN_CUTOFF_ENABLE = 0xEBBA
    VE_REG_INV_OPER_ECO_LOAD_DETECT_PERIODS = 0xEB10
    VE_REG_INV_OPER_ECO_MODE_RETRY_TIME = 0xEB06
    VE_REG_CAPABILITIES1 = 0x0140
