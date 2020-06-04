# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 10:13:40 2020

@author: MajidKhoshrou
"""

# Query all the resources in talkwalker
# See https://apidocs.talkwalker.com/#_how_to_get_the_ids_of_talkwalker_topics

import requests
import json
 url = '*****'
 
response = requests.request("GET", url)
json_data = json.loads(response.text)
all_resources = json_data['result_resources']['projects'][0]    # There is only one project. Something to consider in case later on there more than one projects. 


def GetTalkwalkerID(topic):
  """
  It returns the corresponding Talkwalker ID of a given topic; the topic can be any subject have been set in talkwalker platform under "topics", "filters" or "channels" categories.
  For now there is only one project, therefore all_resources = json_data['result_resources']['projects'][0]. It should be modified for later if there is more than one project.
  """
  
  topic = topic.strip()
  keys_list = ['topics', 'filters','channels']

  results = []
  for k in keys_list:
    try:
      results += list(filter(len,([list(compress(all_resources[k][i]['nodes'],[d['title'] == topic for d in all_resources[k][i]['nodes']])) for i in range(len(all_resources[k]))])))
    except:
      pass
    
  try:
    output = results[0][0].get('id','')
  except:
    output = ''
    
  return output