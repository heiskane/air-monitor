from typing import Union
from datetime import datetime
import json
import paho.mqtt.client as mqtt
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session
from models import Data
from database import SessionLocal


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


def create_db_data(db: Session, *, obj_in: DataSchema) -> Data:
    db_obj = Data(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("data")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    try:
        json_data = json.loads(msg.payload)
    except json.JSONDecodeError:
        print("Failed loading JSON")
        return

    try:
        data = DataSchema(**json_data)
    except ValidationError:
        print("Invalid JSON structure", json_data)
        return
    
    with SessionLocal() as session:
        data.timestamp = datetime.fromtimestamp(data.timestamp)
        db_data = create_db_data(session, obj_in=data)
    
    print(db_data)


def main() -> None:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(username="test_user", password="test_pass")

    client.connect("localhost", 1883, 60)

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()


if __name__ == '__main__':
    main()