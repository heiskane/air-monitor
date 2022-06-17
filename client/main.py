import json
import time
from subprocess import PIPE, Popen
from typing import Dict, Union
from enviroplus import gas
from bme280 import BME280
from ltr559 import LTR559
from smbus import SMBus
from pydantic import BaseModel
import paho.mqtt.client as mqtt
from datetime import datetime


class Data(BaseModel):
    timestamp: int
    oxidised: int
    reduced: int
    nh3: int
    temperature: int
    pressure: int
    humidity: int
    lux: int
    cpu_temp: float
    pm1: float
    pm2_5: float
    pm10: float


def get_cpu_temperature() -> float:
    """Get CPU temperature to use for compensation"""
    process = Popen(
        ["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True
    )
    output, _ = process.communicate()
    return float(output[output.index("=") + 1:output.rindex("'")])


def read_data(bme280: BME280, ltr559: LTR559) -> Dict[str, Union[int, float]]:
    # Compensation factor for temperature
    comp_factor = 2.25
    values = {}
    cpu_temp = get_cpu_temperature()
    values["cpu_temp"] = cpu_temp
    raw_temp = bme280.get_temperature()  # float
    comp_temp = raw_temp - ((cpu_temp - raw_temp) / comp_factor)
    values["temperature"] = int(comp_temp)
    values["pressure"] = int(bme280.get_pressure())
    values["humidity"] = int(bme280.get_humidity())
    gas_data = gas.read_all()
    values["oxidised"] = int(gas_data.oxidising)
    values["reduced"] = int(gas_data.reducing)
    values["nh3"] = int(gas_data.nh3)
    values["lux"] = int(ltr559.get_lux())
    return values


def main() -> None:
    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)
    ltr559 = LTR559()
    client = mqtt.Client()
    client.username_pw_set(username="test_user", password="test_pass")
    client.connect("192.168.1.94", 1883, 60)

    # TODO: Calculate 1min averages to send over mqtt

    while True:
        data = Data(
            timestamp=datetime.utcnow().timestamp(),
            **read_data(bme280, ltr559)
        )
        client.publish("data", json.dumps(data.dict()))
        time.sleep(1)


if __name__ == '__main__':
    main()