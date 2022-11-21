import appdaemon.plugins.hass.hassapi as hass
import mqttapi as mqtt

from json import dumps
from zeep import Client as SoapClient
from zeep.helpers import serialize_object
from datetime import datetime



class KingspanTank:
    def __init__(self, client, tank_info):
        self._client = client
        self._tank_info = tank_info

    def level(self):
        response = self._client.get_latest_level(self._tank_info["SignalmanNo"])
        self._tank_info_items = response["TankInfo"]["APITankInfoItem"]
        level_data = response["Level"]
        return dict(serialize_object(level_data))
        

    def _lookup_tank_info_item(self, item_name):
        if not hasattr(self, "_tank_info_items"):
            self.level()

        for item in self._tank_info_items:
            if item["Name"] == item_name:
                return item["Value"]
        return None

    def serial_number(self):
        return self._lookup_tank_info_item("Serial No")

    def model(self):
        return self._lookup_tank_info_item("Model")

    def name(self):
        return self._lookup_tank_info_item("Tank Name")

    def capacity(self):
        return self._lookup_tank_info_item("Tank Capacity(L)")


class APIError(Exception):
    pass


class SensorClient:
    def __init__(self):
        self._client = SoapClient("https://www.connectsensor.com/soap/MobileApp.asmx?WSDL")
        self._client.set_ns_prefix(None, "http://mobileapp/")

    def login(self, username, password):
        self._username = username
        self._password = password

        self.response = self._client.service.SoapMobileAPPAuthenicate_v3(emailaddress=username, password=password)
        self._tanks = []

        self._user_id = self.response["APIUserID"]
        for tank_info in self.response["Tanks"]["APITankInfo_V3"]:
            self._tanks.append(KingspanTank(self, tank_info))

    def tanks(self):
        return self._tanks

    def get_latest_level(self, signalman_no):
        response = self._client.service.SoapMobileAPPGetLatestLevel_v3(
            userid=self._user_id,
            password=self._password,
            signalmanno=signalman_no,
            culture="en",
        )
        return response


class Tank(mqtt.Mqtt):
    def initialize(self):
        self.sensit_user = self.args["sensit_user"]
        self.sensit_pass = self.args["sensit_pass"]
        self.listen_event(self.first_event, "READ_TANK")

    def first_event(self, event_name, data, kwargs):
        soap_client = SensorClient()
        soap_client.login(self.sensit_user, self.sensit_pass)
        self.log("User: " + self.sensit_user)

        self.log(soap_client.response["APIResult"]["Code"])

        tank = soap_client.tanks()[0]
        # self.log(tank._tank_info["SignalmanNo"])
        # self.log(soap_client._username)
        tank_level = tank.level()
        tank_energy_used = (float(tank.capacity()) - tank_level["LevelLitres"]) * 10.35

        self.log(tank.name() + ":")
        self.log("\tCapacity = {0}".format(tank.capacity()))
        self.log("\tSerial Number = {0}".format(tank.serial_number()))
        self.log("\tModel = {0}".format(tank.model()))
        self.log("\tLevel = {0}% ({1} litres)".format(tank_level["LevelPercentage"], tank_level["LevelLitres"]))
        self.log("\tLast Read = {0}".format(tank_level["ReadingDate"].strftime("%d-%b-%Y %H:%M:%S")))
        self.log("\tRun Out   = {0}".format(tank_level["RunOutDate"].strftime("%d-%b-%Y")))
        self.log("\tEnergy Used = {0}".format(tank_energy_used))

        state_topic = "homeassistant/sensor/tank/state"
        mqtt_fields = [
            {
                "name": "Tank Level",
                "object_id": "tank_level",
                "device_class": "volume",
                "unit_of_measurement": "L",
                "value_template": "{{ value_json.levellitres}}",
                "state_topic": state_topic,
                "state_class": "measurement",
            },
            {
                "name": "Tank Percentage",
                "object_id": "tank_percent",
                "units": "%",
                "value_template": "{{ value_json.levelpercent}}",
                "state_class": "measurement",
                "state_topic": state_topic,
            },
            {
                "name": "Tank Consumption Rate",
                "object_id": "tank_rate",
                "units": "litres/day",
                "value_template": "{{ value_json.consumptionrate}}",
                "state_class": "measurement",
                "state_topic": state_topic,
            },
            {
                "name": "Tank Last Read",
                "object_id": "tank_last_read",
                "units": "",
                "value_template": "{{ value_json.readingdate}}",
                "state_class": "measurement",
                "state_topic": state_topic,
            },
            {
                "name": "Tank Predicted Empty",
                "object_id": "tank_predicted_empty",
                "value_template": "{{ value_json.runoutdate}}",
                "state_class": "measurement",
                "state_topic": state_topic,
            },
            {
                "name": "Tank Energy Used",
                "object_id": "tank_energy",
                "unit_of_measurement": "kWh",
                "value_template": "{{ value_json.energy}}",
                "state_topic": state_topic,
                "state_class": "total_increasing",
                "device_class": "energy",
            },
        ]

        mqtt_values = {
            "levellitres": tank_level["LevelLitres"],
            "levelpercent": tank_level["LevelPercentage"],
            "consumptionrate": float(tank_level["ConsumptionRate"]),
            "readingdate": tank_level["ReadingDate"].strftime("%d-%b-%Y %H:%M:%S"),
            "runoutdate": tank_level["RunOutDate"].strftime("%d-%b-%Y"),
            "energy": tank_energy_used,
        }


        for field in mqtt_fields:
            conf_topic = "homeassistant/sensor/{0}/config".format(field["object_id"])
            conf_payload = dumps(field)
            self.log(conf_topic + ":" + conf_payload)
            self.mqtt_publish(conf_topic, conf_payload, retain=True)

        self.mqtt_publish(state_topic, dumps(mqtt_values), retain=True)
        
        self.log("Done!")

