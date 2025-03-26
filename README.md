# venus.ChargeMeter v1.0.0
This service emulates a smart shunt configured as energy meter and display the data that comes from a configured dbus ac charger.
It is useful if you have and hacked Victron IP22 Smart Charger

![Screenshot 2025-03-25-17-29-36](https://github.com/user-attachments/assets/efbf8796-b063-48a2-8c3d-06462022adef)


### Refrences
* [Venus Wiki](https://github.com/victronenergy/venus/wiki/dbus#temperature)
* [IP22 Hack](https://github.com/pvtex/Victron_BlueSmart_IP22)
* [Smart Shunt VE.Direct](https://www.victronenergy.com/upload/documents/VE.Direct-Protocol-3.33.pdf)



### Configuration

* #### Manual
  See config.sample.ini and amend for your own needs. Copy to `/data/conf` as `charger_meter_config.ini`
    - In `[Setup]` set `debug` to enable debug level on logs, `device` is your charger device to get the data via dbus

### Installation

* #### SetupHelper
    1. install [SetupHelper](https://github.com/kwindrem/SetupHelper)
    2. enter `Package Manager` in Settings
    3. Enter `Inactive Packages`
    4. on `new` enter the following:
        - `package name` -> `ChargerMeter`
        - `GitHub user` -> `mebitek`
        - `GitHub branch or tag` -> `master`
    5. go to `Active packages` and click on `ChargerMeter`
        - click on `download` -> `proceed`
        - click on `install` -> `proceed`

| velib_pyhton available [here](https://github.com/victronenergy/velib_python/tree/master)

### Debugging
You can turn debug off on `config.ini` -> `debug=false`

The log you find in /var/log/ChargerMeter

`tail -f -n 200 /data/log/ChargerMeter/current`

You can check the status of the service with svstat:

`svstat /service/ChargerMeter`

It will show something like this:

`/service/ChargerMeter: up (pid 10078) 325 seconds`

If the number of seconds is always 0 or 1 or any other small number, it means that the service crashes and gets restarted all the time.

When you think that the script crashes, start it directly from the command line:

`python /data/ChargerMeter/ChargerMeter.py`

and see if it throws any error messages.


### Hardware

Tested with:
- Victron IP22 Smart Charger (with VE.Direct hack)
