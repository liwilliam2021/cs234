def get_weather_eval_prompt (original_text, api_candidate): return  [{
                "role": "user",
                "content": f"""
Given a likely inaccurate original text, we want to improve it with an API call. The API response directly following the '→' is always factually correct but other information may not be. It is ok if the augmented generation contradicts the original statement. Respond with 'True' if the augmentation makes the original text more accurate, and 'False' otherwise. Begin your answer with 'True' or 'False' and explain your reasoning on a new line.

Here are a few examples. 

Original Text: Since London is quite chilly today, better wear a jacket.
API Augmentation: Since the weather in London is [WeatherAPI('London')]→overcast clouds, it will take a while for the sun to rise.
True
The Augmentation provides more accurate information. London may not be chilly, but it has overcast clouds according to the WeatherAPI. The reasoning that clouds will delay the sun from rising is also correct. 

Original Text: Tokyo is expected to have a sunny day; it's perfect for a picnic.
API Augmentation: Tokyo is expected to have [WeatherAPI('Tokyo')]→broken clouds and rain showers. The temperature will be around 25°C, with a humidity of about 70%.
False
Tokyo is not expected to have a sunny day because the API response says that there will be broken clouds. However, the Augmentation is not necessarily more accurate because it goes on to conclude things about temperature and humidity that are not substantiated by the API call. 

Original Text: In Mumbai, it's extremely humid and there are chances of thunderstorms later.
API Augmentation: In Mumbai, it's extremely humid and there are chances of thunderstorms later. Output: [WeatherAPI('Mumbai')]→haze:
False
The API Augmentation generates random extra words (eg. 'Output:'). It also concludes that Mumbai is humid without evidence from the API. 

Original Text: Madrid is experiencing scorching heat, stay hydrated and indoors if possible.
API Augmentation: Madrid is experiencing [WeatherAPI('Madrid')]→clear sky and sunny weather.
True
The API Augmentation updates the original text with more factually accurate information from the API. 

Original Text: Oslo is seeing a lot of wind today, secure loose items outdoors.
API Augmentation: Oslo is seeing [WeatherAPI('Orlando')]→clear sky and sunrise at 07:55, which will be the first time in a month that it has seen this.
False
The API Augmentation makes the wrong API call, querying Orlando instead of Oslo. Additionally, it provides information about the sunrise that is not substantiated by the API call. 

Original Text: Los Angeles has perfect weather with mild temperatures and no wind.
API Augmentation: Los Angeles has perfect weather with [WeatherAPI('L.A.')]→Invalid city name or API request failed.
False
The API call fails. 

Please evaluate the following. As a reminder, It is ok if the augmented generation contradicts the original statement.

Original Text: {original_text}
API Augmentation: {api_candidate}

"""
}]

def get_input_generator_prompt (api_candidate): 
  return ([{
      "role": "user",
      "content": f"Generate an input prompt such that the following would be a valid and appropriate output response from a language model. Do not mention the API. Interact with as many details of the output as is appropriate. Respond only with the prompt. \n {api_candidate}"
  }])