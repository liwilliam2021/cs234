from toolformer.utils import ask_gpt
from toolformer.gpt import get_weather_eval_prompt

def score_api_candidate (original_text, api_candidate, human = False):
    
    return_val = None
    if human: # Do human eval
        print ("Candidate:", api_candidate)
        print ("Baseline1:", original_text)
        while True:
            res = input ("Respond with True if the Candidate is better than the Baselines, and False otherwise\n")
            if res == "True": 
              return_val = True
              break
            elif res == "False": 
              return_val = False
              break
            else: print ("Please only respond True or False")
    else:
        messages = [{
            "role": "user",
            "content": f"""
            Given a likely inaccurate original text, we want to improve it with an API call. The API response directly following the '→' is always factually correct but other information may not be. 
            If the augmented generation contradicts the original statement, it is more likely that the augmented generation is correct because it uses the API. Do not penalize the use of the API call. 
            Respond with 'True' if the augmentation makes the original text more accurate, and 'False' otherwise. 
            Begin your answer with 'True' or 'False' and explain your reasoning on a new line."""
        }, {
            "role": "user",
            "content": f"Candidate:{api_candidate}\n Baseline: {original_text}"
        }]
        res = ask_gpt (messages)
        if "True" in res: 
          return_val2 = True
        else:
          return_val2 = False

        if return_val == None: 
          return_val = return_val2
        elif return_val != return_val2:
          print (res)
    
    return return_val


    