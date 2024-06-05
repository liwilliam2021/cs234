# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_api.ipynb.

# %% auto 0
__all__ = ['BaseAPI', 'CalculatorAPI', 'WeatherAPI', 'LocationAPI']

import random
# %% ../nbs/03_api.ipynb 4
from abc import abstractclassmethod

#import wolframalpha
from langchain import PromptTemplate

import pandas as pd
import sys
import subprocess
from datetime import datetime

import logging
#
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] [%(module)s %(funcName)s %(lineno)d] %(message)s",
#     handlers=[
#         logging.FileHandler("debug.log"),
#         logging.StreamHandler()
#     ]
# )

# %% ../nbs/03_api.ipynb 6
class BaseAPI:
    def __init__(
        self,
        name: str, # the name of the API call
        prompt_template: PromptTemplate,
        sampling_threshold: float = 0.2,
        filtering_threshold: float = 0.2,
    ):
        self.name = name
        self.prompt_template = prompt_template
        self.sampling_threshold = sampling_threshold
        self.filtering_threshold = filtering_threshold

    @abstractclassmethod
    def execute(self):
        pass
    
    def __call__(self, *args: str, **kargs: str) -> str:
        output = self.execute(*args, **kargs)
        return str(output)

# %% ../nbs/03_api.ipynb 8
class CalculatorAPI(BaseAPI):
    def execute(self, input: str) -> str:
        try:
            print(f"CalculatorAPI returned from input {input} having eval {eval(input)}")
            return eval(input)
        except:
            return ""

# %% ../nbs/03_api.ipynb 10
# class WolframAPI(BaseAPI):
#     def __init__(self, *args, api_key: str, **kargs):
#         super().__init__(*args, **kargs)
#         self.api_key = api_key
#
#     def execute(self, input: str) -> str:
#         client = wolframalpha.Client(self.api_key)
#         res = client.query(input=input)
#         return next(res.results).text

class TemperatureAPI(BaseAPI):
    def __init__(self, *args, api_key: str, **kargs):
        super().__init__(*args, **kargs)
        self.api_key = api_key
        #raise NotImplementedError


    #def get_temperature(self, latitude: float, longitude: float) -> int:
    #def get_temperature(self, city: str) -> int:
        #client = wolframalpha.Client(self.api_key)
        #res = client.query(input=input)

        # check if city is valid
    def validCity(city: str):
        df = pd.read_csv('../../uscities.csv')
        return (df == city).any().any()

        # command = f"curl -L $(curl -L https://api.weather.gov/points/{latitude},{longitude} | jq --raw-output .properties.forecast) | jq  --raw-output .properties.periods[0].temperature"
        # # print(command)
        # ps = subprocess.Popen(command, shell=True, executable='/bin/bash', stdin=subprocess.DEVNULL,
        #                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # result = ps.stdout.read().decode("utf-8")
        # return int(result)

    def execute(self, input: str) -> str:
        try:
            if self.validCity(input):
                # TODO integrate with temperature API
                return str(random.randint(40, 80))
            else:
                return ""
        except:
            return ""

class WeatherAPI(BaseAPI):
    def __init__(self, *args, api_key: str, **kargs):
        super().__init__(*args, **kargs)
        self.api_key = api_key
        #raise NotImplementedError


    #def get_temperature(self, latitude: float, longitude: float) -> int:
    #def get_temperature(self, city: str) -> int:
        #client = wolframalpha.Client(self.api_key)
        #res = client.query(input=input)

        # check if city is valid
    def validCity(city: str):
        df = pd.read_csv('../../uscities.csv')
        return (df == city).any().any()

        # command = f"curl -L $(curl -L https://api.weather.gov/points/{latitude},{longitude} | jq --raw-output .properties.forecast) | jq  --raw-output .properties.periods[0].temperature"
        # # print(command)
        # ps = subprocess.Popen(command, shell=True, executable='/bin/bash', stdin=subprocess.DEVNULL,
        #                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # result = ps.stdout.read().decode("utf-8")
        # return int(result)

    def execute(self, input: str) -> str:
        # now sure how to handle generic string text, when the weatherAPI requires specific inputs
        try:
            if self.validCity(input):
                # TODO integrate with weather API
                # weatherAPI.com, api key: ecfeef9758ff455084241925242105
                options = [ "Sunny",
                            "Cloudy",
                            "Rainy",
                            "Snowy",
                            "Windy",
                            "Stormy",
                            "Foggy",
                            "Hail",
                            "Sleet",
                            "Thunderstorm"
                            ]
                return random.choice(options)
            else:
                return ""
        except:
            return ""


class LocationAPI(BaseAPI):
    def __init__(self, *args, cities_csv: str, **kargs):
        super().__init__(*args, **kargs)
        self.df = pd.read_csv(cities_csv)
        #self.api_key = api_key


    def execute(self, input: str) -> str:
        input = input.strip()
        input = input.replace("'","")
        input = input.replace('"', '')
        result = self.df.loc[:, ['city', 'state_name']][self.df['city'] == input]
        # return result.size
        #with open('logs/qa_location.txt', 'a') as f:
        #logging.info(f"{datetime.now()}: checking input {input}")
            #print(f"{datetime.now()}: checking input {input}", file=f)
        if len(result) > 0:
            # with open('alfred/log.txt', 'a') as f:
            #     print(f"returning from api {result.iloc[0]['state_name']}", file=f)
            #print(f"LocationAPI returned value with city {input} having state {result.iloc[0]['state_name']}")
            logging.info(f"LocationAPI returned value with city={input} having state={result.iloc[0]['state_name']}")
            return result.iloc[0]['state_name']
        else:
            return ""




class SearchAPI(BaseAPI):
    def __init__(self, *args, api_key: str, **kargs):
        super().__init__(*args, **kargs)
        #self.api_key = api_key
        raise NotImplementedError
