# ha_sensit
Appdaemon app to read a Kingspan Sensit tank meter and write to Home Assistant via MQTT

<H1>AppDaemon and MQTT Installation</H1>

Install [AppDaemon](https://appdaemon.readthedocs.io/en/latest/INSTALL.html)<br>
Install [Mosquitto MQTT Broker](https://github.com/home-assistant/addons/tree/master/mosquitto)<br>
Configure [AppDaemon's HASS and MQTT plugins](https://appdaemon.readthedocs.io/en/latest/CONFIGURE.html): the *appdaemon.yaml* file in this repo
should have most of the configuration required.<br>

Install [MQTT Explorer](http://mqtt-explorer.com/) or equivalent somewhere on your network so you can check the MQTT broker is working correctly.<br>

At this point you might want to write a simple AppDaemon app to check that it is working properly and that it can talk to your MQTT broker. 
There are some useful guides [here](https://medium.com/@marcelblijleven/appdaemon-part-1-e63d1bffe7ca) and
[here](https://webworxshop.com/getting-started-with-appdaemon-for-home-assistant/)<br>

<H1>The Tank App</H1>
Copy *tanks.py* from the *apps* folder to *config/appdaemon/apps*<br>
Merge the contents of *apps.yampl* into the *apps.yaml* file in *config/appdaemon/apps*<br>
Add two secrets to your *config/secrets.yaml* file:<br>

    sensit_user: email_address_from_sensit_app
    sensit_pass: password_from_sensit_app

Open the [AppDaemon Main Log](http://homeassistant.local:5050/aui/index.html#/logs). Your should see the following:<br>
`2022-11-07 17:37:25.127050 INFO AppDaemon: Initializing app tank using class Tank from module tank`

<h1>Test Trigger the App with an Event</h1>
In a separate browser window go to [HA Developer Tools](http://homeassistant.local:8123/developer-tools/event):

    Event Type*: READ_TANK
    
Click on: **FIRE EVENT**<br>

Back in the Appdaemon Log window you should see something like:

    2022-11-07 19:40:43.960708 INFO tank: Done!
    2022-11-07 19:40:43.940654 INFO tank: homeassistant/sensor/tank_energy/config:{"name": "Tank Energy Used", "object_id": "tank_energy", "unit_of_measurement": "kWh", "value_template": "{{ value_json.energy}}", "state_topic": "homeassistant/sensor/tank/state", "state_class": "total_increasing", "device_class": "energy"}
    2022-11-07 19:40:43.923549 INFO tank: homeassistant/sensor/tank_predicted_empty/config:{"name": "Tank Predicted Empty", "object_id": "tank_predicted_empty", "value_template": "{{ value_json.runoutdate}}", "state_class": "measurement", "state_topic": "homeassistant/sensor/tank/state"}
    2022-11-07 19:40:43.896472 INFO tank: homeassistant/sensor/tank_last_read/config:{"name": "Tank Last Read", "object_id": "tank_last_read", "units": "", "value_template": "{{ value_json.readingdate}}", "state_class": "measurement", "state_topic": "homeassistant/sensor/tank/state"}
    2022-11-07 19:40:43.876574 INFO tank: homeassistant/sensor/tank_rate/config:{"name": "Tank Consumption Rate", "object_id": "tank_rate", "units": "litres/day", "value_template": "{{ value_json.consumptionrate}}", "state_class": "measurement", "state_topic": "homeassistant/sensor/tank/state"}
    2022-11-07 19:40:43.856673 INFO tank: homeassistant/sensor/tank_percent/config:{"name": "Tank Percentage", "object_id": "tank_percent", "units": "%", "value_template": "{{ value_json.levelpercent}}", "state_class": "measurement", "state_topic": "homeassistant/sensor/tank/state"}
    2022-11-07 19:40:43.847321 INFO tank: homeassistant/sensor/tank_level/config:{"name": "Tank Level", "object_id": "tank_level", "device_class": "volume", "unit_of_measurement": "L", "value_template": "{{ value_json.levellitres}}", "state_topic": "homeassistant/sensor/tank/state", "state_class": "measurement"}
    2022-11-07 19:40:43.845510 INFO tank: Energy Used = 7948.799999999999
    2022-11-07 19:40:43.843775 INFO tank: Run Out = 02-Feb-2023
    2022-11-07 19:40:43.842107 INFO tank: Last Read = 07-Nov-2022 00:55:16
    2022-11-07 19:40:43.840396 INFO tank: Level = 45% (682 litres)
    2022-11-07 19:40:43.838555 INFO tank: Model = Unknown
    2022-11-07 19:40:43.836844 INFO tank: Serial Number = 2000xxxx
    2022-11-07 19:40:43.835014 INFO tank: Capacity = 1450
    2022-11-07 19:40:43.833025 INFO tank: Your Tank Name:
    2022-11-07 19:40:42.748583 INFO tank: 0
    2022-11-07 19:40:42.747518 INFO tank: User: youruser@something.com

This means that the app has successfully logged into Sensit and downloaded the tank data (bottom 10 lines) and then written the data to the MQTT broker (top 7 lines).<br>

In **MQTT Explorer** connect to your HA MQTT Broker. You should see:

    192.168.x.x
        homeassistant
            sensor
                tank(1 topic, 1 message)
      

