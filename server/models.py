from sqlalchemy import Column, DateTime, Float, Integer

from database import Base

class Data(Base):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    oxidised = Column(Integer)
    reduced = Column(Integer)
    nh3 = Column(Integer)
    temperature = Column(Integer)
    pressure = Column(Integer)
    humidity = Column(Integer)
    lux = Column(Integer)
    cpu_temp = Column(Float)