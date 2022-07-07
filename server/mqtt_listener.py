from time import sleep
from typing import Optional, Union
from datetime import datetime
import json
import paho.mqtt.client as mqtt
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from models import Data
from database import SessionLocal
from config import settings
import logging


logging.basicConfig(format='%(asctime)s %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DataSchema(BaseModel):
    timestamp: Union[int, datetime]
    oxidised: int
    reduced: int
    nh3: int
    temperature: int
    pressure: int
    humidity: int
    lux: int
    cpu_temp: float
    pm1: Optional[float]
    pm2_5: Optional[float]
    pm10: Optional[float]


def create_db_data(db: Session, *, obj_in: DataSchema) -> Data:
    db_obj = Data(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("data")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        json_data = json.loads(msg.payload)
    except json.JSONDecodeError:
        logger.error("Failed loading JSON")
        return

    try:
        data = DataSchema(**json_data)
    except ValidationError:
        logger.error("Invalid JSON structure", json_data)
        return
    
    with SessionLocal() as session:
        data.timestamp = datetime.fromtimestamp(data.timestamp)
        create_db_data(session, obj_in=data)
    
    logger.info(f"Adding data: {data}")


def main() -> None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(
        username=settings.MQTT_USERNAME,
        password=settings.MQTT_PASSWORD
    )

    try:
        client.connect(settings.MQTT_SERVER, 1883, 60)
    except ConnectionRefusedError:
        logger.error("Failed connectiong to mqtt server. Trying again in 3 seconds")
        sleep(3)
        main()

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()


if __name__ == '__main__':
    main()