# -*- coding: utf-8 -*-
"""
Created on Thu Jun  4 10:13:40 2020

@author: MajidKhoshrou
"""

# Query all the resources in talkwalker
# See https://apidocs.talkwalker.com/#_how_to_get_the_ids_of_talkwalker_topics

#How to get the IDs of Talkwalker topics?
#To get a list of the topics defined in a Talkwalker project use the project_id and the access_token on the https://api.talkwalker.com/api/v2/talkwalker/p/<project_id>/resources endpoint. Optionally, the filter type can be set if we want to obtain only search-topics: type=search
#
#curl -XGET 'https://api.talkwalker.com/api/v2/talkwalker/p/<project_id>/resources?access_token=<access_token>&type=search'
#The result, using the above filter, has the form:
#
#{
#  "status_code" : "0",
#  "status_message" : "OK",
#  "request" : "GET /api/v3/talkwalker/p/<project_id>/resources?access_token=<access_token>&type=search",
#  "result_resources" : {
#    "projects" : [ {
#      "id" : "<project_id>",
#      "title" : "Air France",
#      "topics" : [ {
#        "id" : "2p1nevfo_121244b12ade",
#        "title" : "Category 1",
#        "nodes" : [ {
#          "id" : "l9gb1vj7_9utd4cawszq7",
#          "title" : "topic 1"
#        }, {
#          "id" : "g8wf5sd4_8svs0cfghje8",
#          "title" : "topic 2"
#        } ]
#      }, {
#        "id" : "kj241kj4_h214jhv21l2a",
#        "title" : "Catergory 2",
#        "nodes" : [ {
#          "id" : "w6fc8sf4_4fds6hdgsjd1",
#          "title" : "topic 1"
#        } ]
#      } ]
#    } ]
#  }
#}
#To get results for all projects in 'search' use search as topic ID. To use a single topic, use the ID of the topic (for example w6fc8sf4_4fds6hdgsjd1 for topic 1 of category 2).
#

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