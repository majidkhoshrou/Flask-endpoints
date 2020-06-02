# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 17:47:13 2020

@author: MajidKhoshrou
"""

@ns.route('/target_movement_twitter/<search_words>, <language>, <result_type>', methods=['GET'])
@ns.doc(params={"search_words":"startup" , "language": "en", "result_type":"popular"})
class GetTargetMovementTwitter(Resource):

    #@ns.expect(twitter_request_obj, skip_none=False)
    def get(self, search_words, language, result_type):   
        """
        GET request to retrieve tweets.

        "result_type" can be popular, recent or mixed tweets containing a hashtag or keyword.
        For the free Twitter API access, only the data for the past seven days are available.
        """
        consumer_key = config.twitter_api_credentials["consumer_key"]
        consumer_secret = config.twitter_api_credentials["consumer_secret"]
        access_token = config.twitter_api_credentials["access_token"]
        access_token_secret = config.twitter_api_credentials["access_token_secret"] 
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret);        
        auth.set_access_token(access_token, access_token_secret);
        api = tweepy.API(auth, wait_on_rate_limit=True) ;        
        
        #input_params = ns.payload
        #search_words =  input_params['search_words']                 
        #language =  input_params['language']     # Language code (follows ISO 639-1 standards)
        #until_date =  input_params['until_date']
        #result_type = input_params['result_type']  until=until_date

        try:
            results =  tweepy.Cursor( api.search, q=search_words, lang=language, result_type = result_type).items(10)            
            out = { tweet.user.screen_name: { "followers_count": tweet.user.followers_count, \
                "location": tweet.user.location ,"favorite_count":tweet.favorite_count,"text": tweet.text} for tweet in results }
            sorted_keys = {k:v["followers_count"] for (k,v) in out.items()}
            sorted_keys = sorted(sorted_keys, key=sorted_keys.__getitem__, reverse=True)
            out = {k:out[k] for k in sorted_keys}
            return out
        except tweepy.error.TweepError as e:
            return(json.loads(e.response.text)['errors'][0]['message'], 401)



@ns.route('/twitter_trends/<woe_id>', methods=['GET'])
@ns.doc(params={"woe_id":"Enter a woe id, e.g., 733075"})
class TwitterTrends(Resource):

    def get(self, woe_id):
        """
        Get request that returns top current trends on twitter for a given place. 
        The Where On Earth ID  (WOEID) should be provided.
        More info in http://benalexkeen.com/interacting-with-the-twitter-api-using-python/

        """
        
        consumer_key = config.twitter_api_credentials["consumer_key"]
        consumer_secret = config.twitter_api_credentials["consumer_secret"]
        access_token2 = config.twitter_api_credentials["access_token"]
        access_token_secret = config.twitter_api_credentials["access_token_secret"] 

        key_secret = '{}:{}'.format(consumer_key, consumer_secret).encode('ascii')
        b64_encoded_key = base64.b64encode(key_secret)
        b64_encoded_key = b64_encoded_key.decode('ascii')

        base_url = config.twitter_api_credentials["base_url_auth"]
        auth_url = '{}oauth2/token'.format(base_url)
        auth_headers = {'Authorization': 'Basic {}'.format(b64_encoded_key),
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
        auth_data = {'grant_type': 'client_credentials'}
        auth_resp = requests.post(auth_url, headers=auth_headers, data=auth_data)
        access_token = auth_resp.json()['access_token']
        
        search_headers = { 'Authorization': 'Bearer {}'.format(access_token) }
        base_url = config.twitter_api_credentials["base_url_trend"]
        url = base_url + woe_id
        response = requests.get(url, headers=search_headers)
        tweet_data = response.json()
        return tweet_data

#@ns.route('/target_movement_twitter')
        
    
    
    
    