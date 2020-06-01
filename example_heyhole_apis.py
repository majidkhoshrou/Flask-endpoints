# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 17:26:39 2020

@author: MajidKhoshrou
"""

import json
from cognitiveapi import config
from flask_restplus import Namespace
from flask import request, jsonify
import requests
from flask import Flask , abort
from flask_restplus import Api, Resource, fields
from sent_app import polarity_apis, ml
from cognitiveapi.logger import debug
from sent_app.models import keyhole_request_obj , keyhole_create_tracker, keyhole_tracker_update, keyhole_retrieve_batch_obj 
from sent_app.models import twitter_request_obj, twitter_trend_obj, yahoo_weather_obj
from sent_app.models import keyhole_target_emotion_obj , keyhole_influencers_obj

import tweepy
import base64
from scipy.stats import norm
import numpy
import urllib3
import time, uuid, urllib, json
import hmac, hashlib
from base64 import b64encode
from functools import reduce
from operator import getitem
import logging

import pyodbc


#Some links:
##  https://github.com/joelverhagen/flask-rauth/blob/master/example/facebook.py
##  http://docs.tweepy.org/en/v3.8.0/api.html#api-reference ##
##  https://gist.github.com/dev-techmoe/ef676cdd03ac47ac503e856282077bf2  ## what attributes we can get

ns = Namespace('target_movement', path='/', description='All low_level endpoints for target tracking are here.')
    
@ns.route('/keyhole_influencers_data/<hash>, <sort_type>, <limit>, <page>, <days>', methods=['GET'])
@ns.doc(params={"sort_type":"engagement","limit":"10", "page":"1", "hash":"17jlMB", "days":"7"})
class KeyholeInfluencersData(Resource):

    def get(self, hash, sort_type, limit, page, days):
        """
        GET request to retrieve influencers data from a tracker that you own.

       The required parameter "hash" is the tracker id; the "days" parameter can be\
       set to get data from a few days to a few month back (days: [1, 7, 14, 30, 90]); \
       in case of setting the "start" (date), "end" (date) needs to be set. In the previous case Keyhole \
       ignores the "days" parameter. The parameter "limit"  (default:10) specifies the number of records to \
       be retrieved.
       The parameter "sort_type" can get "posts" or "engagemnt" values; it specifies the type of influencers data\
       to be retrieved (default: "engagement").
        """ 
        base_url = config.keyhole_credentials["base_url"]
        if hash is None:
            return "Hash parameter (tracker id) is required!", 400
        url = base_url + hash + "/"+ "batch"
        querystring = {"hash":hash, "limit":limit, "days":days, "page": page} 
        querystring["access_token"] = config.keyhole_credentials["access_token"]
        querystring["metrics"] = "influencers"
        response = requests.request("GET", url, params = querystring) 
        json_data = json.loads(response.text)
        if response.status_code != 200:
            return json_data["message"], response.status_code
        else:
            results =[] 

            if  sort_type not in ["engagement", "posts"]:
                return "sort_type value must be in either engagement or posts.", 400
            influencers_data = json_data["data"]["influencers"]["influencers_by_"+sort_type]
            output={}
            for i in range(min(len(influencers_data),10)):                
                output["platform"+str(i)] = RetrieveBatchedTrackerData.get_item_list_dict(self, 'json_data["data"]["influencers"]["influencers_by_"+var1][iter1]["platform"]', json_data=json_data, iter1=i, var1=sort_type)
                output["username"+str(i)] = RetrieveBatchedTrackerData.get_item_list_dict(self,'json_data["data"]["influencers"]["influencers_by_"+var1][iter1]["username"]', json_data=json_data, iter1=i, var1=sort_type)
                output["counts"+str(i)] = RetrieveBatchedTrackerData.get_item_list_dict(self, 'json_data["data"]["influencers"]["influencers_by_"+var1][iter1]["counts"]', json_data=json_data, iter1=i, var1=sort_type)
                output["posts"+str(i)] = {RetrieveBatchedTrackerData.get_item_list_dict(self, 'json_data["data"]["influencers"]["influencers_by_"+var1][iter1]["posts"][iter2]["id"]', json_data=json_data, iter1=i,iter2=j,var1=sort_type):\
                    RetrieveBatchedTrackerData.get_item_list_dict(self, 'json_data["data"]["influencers"]["influencers_by_"+var1][iter1]["posts"][iter2]["post_url"]', json_data=json_data, iter1=i, iter2=j,var1=sort_type) \
                    for j in range(min(10, len(influencers_data[i]["posts"])))}

            return output

@ns.route('/retrieve_batched_tracker_data/<days>, <platforms>, <hash>,<country_locations>', methods=['GET'])
@ns.doc(params={"days":"7", "platforms":"twitter, instagram, blogs, news or all", "hash":"17jlMB",\
    "country_locations":"e.g., CA,GB. To clear location settings, false may be passed."})
class RetrieveBatchedTrackerData(Resource):
    
    """
    
    Here we retrieve some nested json data from Keyhole API. Some custom functions have been defined to faciliate that.
    """
    
    def MoodScoreFromSentiment(self, pos, neu, neg):
        """
        Gets 3 measures of the nubmer of positive, neutral and negative posts and returns a normalize score.
        """
        pos, neu, neg = norm.cdf([pos, neu, neg], loc=neu, scale = numpy.std([pos, neu, neg]))
        mood_score = neu + pos - neg
        mood_score = max(mood_score,0) and min(mood_score, 1) # limit between [0,1]
        return mood_score

    def get_item_nested_dict(self, data, keys):
        """Obtaines the value in a nested dictionary. In case of exception returns an empty string."""
        try:
            return reduce(getitem, keys, data)
        except Exception as e:  
            template = " An exception of type < {0} > occurred ==> Arguments: {1!r} ==> {2}"  
            message = template.format(type(e).__name__, e.args, keys)
            logging.error(message)
            return ""

    def get_item_list_dict(self, arg2eval, json_data=None, iter1=None, iter2=None, var1=None):
        """
        Get data from a list inside a nested dictionary. json_data should have the same name as 
        the json data outside the function.
        """
        try: 
            return eval(arg2eval)
        except Exception as e:
            template = " An exception of type < {0} > occurred ==> Arguments: {1!r} ==> {2}"
            message = template.format(type(e).__name__, e.args, arg2eval)
            logging.error(message)
            return ""

    def get(self, days, platforms, hash, country_locations):
        """
        GET request to retrieve multiple data metrics from a tracker that you own.
        See https://apidocs.keyhole.co/ for more info.
        """ 
        base_url = config.keyhole_credentials["base_url"]
        if hash is None:
            return "Hash parameter (tracker id) is required!", 400
        url = base_url + hash + "/"+ "batch"
        
        querystring = { "days":days, "hash":hash } if platforms == "all" else { "days":days, "platforms":platforms, "hash":hash }
        querystring["country_locations"] = country_locations
        querystring["access_token"] = config.keyhole_credentials["access_token"]
        querystring["metrics"] = "timeline, demographics, sentiment, geography, postType, links"
        response = requests.request("GET", url, params = querystring) 
        json_data = json.loads(response.text)
        if response.status_code != 200:
            return json_data["message"], response.status_code
        else:
            output ={}
            pos, neu, neg = list(json_data["data"]["sentiment"].values())
            mood_score = self.MoodScoreFromSentiment(pos, neu, neg)

            output["tracker_id"] = hash
            output["metrics_movement"] = self.get_item_nested_dict(json_data, ["data", "timeline", "counts", "posts"])
            output["metrics_mood"] = "{0:1.2f}".format(mood_score) 

            output["timeline_counts_posts"] = self.get_item_nested_dict(json_data, ["data","timeline","counts","posts"])
            output["timeline_counts_users"] = self.get_item_nested_dict(json_data,["data","timeline","counts","users"])
            output["timeline_counts_engagements"] = self.get_item_nested_dict(json_data,["data","timeline","counts","engagements"])
            output["timeline_counts_impressions"] = self.get_item_nested_dict(json_data,["data","timeline","counts","impressions"])
            output["timeline_counts_reach"] = self.get_item_nested_dict(json_data,["data","timeline","counts","reach"])
            output["demographics_male"] = self.get_item_nested_dict(json_data,["data","demographics","male"])
            output["demographics_female"] =self.get_item_nested_dict(json_data,["data","demographics","female"])  
            
            output["geography_countries_country_1"] = self.get_item_list_dict('json_data["data"]["geography"]["countries"][iter1]["country"]', json_data=json_data, iter1=0)
            output["geography_countries_count_1"] =  self.get_item_list_dict('json_data["data"]["geography"]["countries"][iter1]["count"]', json_data=json_data, iter1=0)
            output["geography_countries_country_2"] =  self.get_item_list_dict('json_data["data"]["geography"]["countries"][iter1]["country"]', json_data=json_data, iter1=1)
            output["geography_countries_count_2"] =   self.get_item_list_dict('json_data["data"]["geography"]["countries"][iter1]["count"]', json_data=json_data, iter1=1)
            output["postType_original"] = self.get_item_nested_dict(json_data, ["data","postType","original"])
            output["postType_retweet"] = self.get_item_nested_dict(json_data, ["data","postType","retweet"])
            output["postType_reply"] = self.get_item_nested_dict(json_data, ["data","postType","reply"])

            output["links_top_domains_domain_1"] = self.get_item_list_dict('json_data["data"]["links"]["top_domains"][iter1]["domain"]', json_data=json_data, iter1=0)
            output["links_top_domains_count_1"] = self.get_item_list_dict('json_data["data"]["links"]["top_domains"][iter1]["count"]', json_data=json_data, iter1=0)
            output["links_top_domains_domain_2"] = self.get_item_list_dict('json_data["data"]["links"]["top_domains"][iter1]["domain"]', json_data=json_data, iter1=1)
            output["links_top_domains_count_2"] = self.get_item_list_dict('json_data["data"]["links"]["top_domains"][iter1]["count"]', json_data=json_data, iter1=1)
            output["links_top_links_link_1"] = self.get_item_list_dict('json_data["data"]["links"]["top_links"][iter1]["link"]', json_data=json_data, iter1=0)
            output["links_top_links_count_1"] = self.get_item_list_dict('json_data["data"]["links"]["top_links"][iter1]["count"]', json_data=json_data, iter1=0)
            output["links_top_links_link_2"] = self.get_item_list_dict('json_data["data"]["links"]["top_links"][iter1]["link"]', json_data=json_data, iter1=1)
            output["links_top_links_count_2"] = self.get_item_list_dict('json_data["data"]["links"]["top_links"][iter1]["count"]', json_data=json_data, iter1=1)
            
            return output

@ns.route('/target_emotion_metrics/<days>, <platforms>, <hash>', methods=['GET'])
@ns.doc(params={"days":"7", "platforms":"twitter, instagram, blogs, news or all", "hash":"17jlMB"})
class TargetEmotionMetrics(Resource):
    def get(self, days, platforms, hash):
        """
        Returns the target emotion metrices.

        days: The trailing date range window in days (possible values: 1, 7, 14, 30, 60).\
        platforms: A comma separated list of platforms to retrieve data from. Current platforms are twitter, instagram, blogs, news and forums.
        """  
        base_url = config.keyhole_credentials["base_url"]   
        if hash is None:
            return "Hash parameter (tracker id) is required!", 400
        url = base_url + hash + "/"+ "batch"
        
        querystring = { "days":days, "hash":hash } if platforms == "all" else { "days":days, "platforms":platforms, "hash":hash }
        querystring["access_token"] = config.keyhole_credentials["access_token"]
        querystring["metrics"] = "timeline, sentiment"
        response = requests.request("GET", url, params = querystring) 
        json_data = json.loads(response.text)
        if response.status_code != 200:
            return json_data["message"], response.status_code
        else:
            output ={}
            pos, neu, neg = list(json_data["data"]["sentiment"].values())
            mood = RetrieveBatchedTrackerData.MoodScoreFromSentiment(self, pos, neu, neg) 
            movement = RetrieveBatchedTrackerData.get_item_nested_dict(self,json_data, ["data", "timeline", "counts", "posts"])
           
            mood_color= "red" if mood<0.4 else "green" if mood>.6 else "yellow" if ~numpy.isnan(mood) else str(mood).lower()
            movement_color = "green" if movement != 0 else 'red' 

            output["tracker_id"] = hash
            output["movement"] = movement
            output["movement_colour"] = movement_color
            output["mood"] = "{0:1.3f}".format(mood) 
            output["mood_colour"] = mood_color

            return output


@ns.route('/retrieve_tracker_data/<days>, <limit>, <page>, <hash>, <metric>', methods=['GET'])
@ns.doc(params={"days":"7","limit":"10", "page":"1", "hash":"17jlMB", "metric":"sentiment"})
class RetrieveTrackerData(Resource):
    def get(self, hash, days, limit, page, metric):
        """
        GET request to retrieve metric data from a tracker that you own.
        See https://apidocs.keyhole.co/
        """  
        base_url = config.keyhole_credentials["base_url"]   
   
        if hash is None:
            return "Hash parameter (tracker id) is required!", 400
        elif metric is None:
            return "Metric parameter is required!", 400
        else:
            pass
        url = base_url + hash + "/"+ metric
        querystring = {"hash":hash, "limit":limit, "page":page, "metric":metric, "days":days }
        querystring["access_token"] = config.keyhole_credentials["access_token"]
        response = requests.request("GET", url, params = querystring) 
        json_data = json.loads(response.text)
        if response.status_code != 200:
            return json_data["message"], response.status_code
        else:
            output = json_data
            return output       










    

