
import os
import re

from sqlalchemy import Column,String,Integer,ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event

import pandas as pd

from . import config

eng = create_engine(config.config("DB_URI"))
sm = sessionmaker(bind=eng)
Base = declarative_base(bind=eng)

def connect():
    return eng.connect()

def get_session():
    return sm()

class Variable(Base):
    """
    A variable, associating values with mappings and a description
    """
    __tablename__ = "variables"
    id = Column(Integer,primary_key=True)
    name = Column(String,unique=True)
    description = Column(String)
    mappings = relationship("Mapping",back_populates="variable")
    def __repr__(self):
        print(f"{self.name}")

class Mapping(Base):
    """
    Integer -> String mapping for descriptive values
    Used for Domain -> Range when making plots.
    """
    __tablename__ = "mappings"
    id = Column(Integer,primary_key=True)
    variable_id = Column(Integer,ForeignKey("variables.id"))
    variable = relationship("Variable",back_populates="mappings")
    key = Column(Integer)
    value = Column(String)
    def __repr__(self):
        print(f"Mapping 4 {self.variable.name}")

sqlcol = lambda x: re.sub("[^a-zA-Z_0-9]+","",x)

def getvar(vname,connection):
    return pd.read_sql(f"SELECT {sqlcol(vname)} FROM data",connection)

def withmeta(series,session):
    mappings = getdict(series.name,session)
    series = (series
            .apply(lambda x: mappings.get(x))
            .astype("category")
        )
    
    revmap = {v:k for k,v in mappings.items()}

    levels = list(mappings.values())
    levels.sort(key = lambda lvl: revmap[lvl]) 
    series.levels = levels 

    return series 

def getdict(variable,session):
    var = session.query(Variable).filter(Variable.name == variable).first()
    return {mp.key:mp.value for mp in var.mappings}

def getdescr(vname,session):
    return session.query(Variable).filter(Variable.name == vname).first().description
