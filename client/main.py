import json
import time
from subprocess import PIPE, Popen
from typing import Dict
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


def get_cpu_temperature() -> float:
    """Get CPU temperature to use for compensation"""
    process = Popen(
        ["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True
    )
    output, _ = process.communicate()
    return float(output[output.index("=") + 1:output.rindex("'")])


def read_data(bme280: BME280, ltr559: LTR559) -> Dict[str, int]:
    # Compensation factor for temperature
    comp_factor = 2.25
    values = {}
    cpu_temp = get_cpu_temperature()
    raw_temp = bme280.get_temperature()  # float
    comp_temp = raw_temp - ((cpu_temp - raw_temp) / comp_factor)
    values["temperature"] = int(comp_temp)
    values["pressure"] = round(
        int(bme280.get_pressure() * 100), -1
    )  # round to nearest 10
    values["humidity"] = int(bme280.get_humidity())
    data = gas.read_all()
    values["oxidised"] = int(data.oxidising)
    values["reduced"] = int(data.reducing)
    values["nh3"] = int(data.nh3)
    values["lux"] = int(ltr559.get_lux())
    return values


def main() -> None:
    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)
    ltr559 = LTR559()
    client = mqtt.Client()
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