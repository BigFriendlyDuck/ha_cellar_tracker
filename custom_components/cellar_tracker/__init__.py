from cellartracker import cellartracker
import pandas as pd
import numpy as np
import logging

from random import seed
from random import randint
from datetime import timedelta

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle




"""Example Load Platform integration."""
DOMAIN = 'cellar_tracker'

SCAN_INTERVAL = timedelta(seconds=3600)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=3600)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Your controller/hub specific code."""
    # Data that you want to share with your platforms
    
    conf = config[DOMAIN]
    
    username = conf[CONF_USERNAME]
    password = conf[CONF_PASSWORD]
    

    
    hass.data[DOMAIN] = WineCellarData(username, password)
    hass.data[DOMAIN].update()


    
    hass.helpers.discovery.load_platform('sensor', DOMAIN, {}, config)
    

    return True

class WineCellarData:
    """Get the latest data and update the states."""

    def __init__(self, username, password):
        """Init the Canary data object."""

        self._username = username
        self._password = password
        

    def get_reading(self, key):
      return self._data[key]

    def get_readings(self):
      return self._data

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
      data = {}
      username = self._username
      password = self._password


      client = cellartracker.CellarTracker(username, password)
      list = client.get_inventory()
      df = pd.DataFrame(list)
      df[["Price","Valuation"]] = df[["Price","Valuation"]].apply(pd.to_numeric)
      
      group_data = df.groupby(["iWine"]).agg({'Wine': ['count', 'first'], 'Valuation': ['sum', 'mean'], 'Appellation': 'first','Vintage': 'first', 'Color': 'first', 'BeginConsume':'first','EndConsume':'first'})
      group_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in group_data.columns.values]
      for row_main, item_main in group_data.iterrows():
          # the name represents the group
          name = item_main['Wine_first'] + '_' + item_main['Vintage_first']
          data[name] = {}
          data[name][row_main] = {"count": item_main['Wine_count'], "value_total": item_main['Valuation_sum'],
                             "value_avg": item_main['Valuation_mean'], "%": 1}
          data[name][row_main]["Wine Name"] = item_main['Wine_first']
          data[name][row_main]["Vintage"] = item_main['Vintage_first']
          data[name][row_main]["Colour"] = item_main['Color_first']
          data[name][row_main]["Appellation"] = item_main['Appellation_first']
          data[name][row_main]["Best after"] = item_main['BeginConsume_first']
          data[name][row_main]["Best before"] = item_main['EndConsume_first']

      data["total_bottles"] = len(df)
      data["total_value"] = df['Valuation'].sum()
      data["average_value"] = df['Valuation'].mean()
      self._data = data
