from twitter import Twitter, OAuth, TwitterHTTPError
import time
from datetime import datetime, timedelta
import pandas as pd
from pandas import json_normalize
import re
from dateutil import parser
import lxml.etree as etree
import json

keys = [{"token":"", "token_secret":"",
		"consumer_key":"", "consumer_secret": ""}]

api_list = []
for key in keys:
	api_list.append(Twitter(auth = OAuth(*key.values())))

class twTool():
	"""
	This Tool compares two hashtags with one another. Inputs:
	query1: string
	query2: string
	since: date as string, default False
	until: date as string, default False
	howmany: int of how many tweets to query, default 0
	search_option: wether or not to look for both hashtags seperately. default False
	"""
	def __init__(self, query1: str, query2: str, since=False, until=False, howMany: int=0, search_option=False):
		self.querys = []
		for x in (query1, query2):
			if x[0] == "#":
				self.querys.append(x)
			else:
				self.querys.append("#" + x)
		if since:
			self.since = parser.parse(since).date()
		else:
			self.since = False
		if until:
			self.until = parser.parse(until).date()
		else:
			self.until = False

		if howMany > 0:
			self.howMany_option = True
		else:
			self.howMany_option = False
		self.howMany = int(howMany/100)

		self.search_option = search_option

		self.results_raw = []
		self.results_1 = []
		self.results_2 = []
		self.results_same = []

		self.hashtag_list = []

		self.api_list = []
		self.error = False
		self.number_of_tweets = 0
		self.end_message = ""
		self._search()

	def _search(self):
		"""
		This function carries out the Twitter search via the Twitter API.
		The logic of the search is determined by the parameters with which the class is called.
		It calls _sort() when it's finished.
		"""
		global api_list
		#search parameters
		params_1 = dict(include_entities=True, tweet_mode="extended", result_type="recent", count=100)
		params_2 = dict(include_entities=True, tweet_mode="extended", result_type="recent", count=100)
		if self.since:
			params_1["until"] = self.since
		if not self.search_option:
			params_1["q"] = self.querys[0]+" OR "+self.querys[1]
			params_2["q"] = self.querys[0]+" OR "+self.querys[1]
		#api key to use
		api_number = 0
		api = api_list[api_number]
		counter = 0

		results_raw = []
		#check for search_option
		if self.search_option:				
			#check for howMany
			if self.howMany_option:
				#check for each query
				for query in self.querys:
					#for chosen sample size
					for x in range(self.howMany):
						try:
							#first search with since
							if counter == 0:
								result = api.search.tweets(q=query, **params_1)
								#check for 0 results
								if len(result["statuses"]) == 0:
									break
									self.end_message = "Search ended because no more tweets were found."
								maxId = self._search_extension(result)
								counter += 1
							#all following searches
							else:
								result = api.search.tweets(q=query, max_id=maxId-1, **params_2)
								if len(result["statuses"]) == 0:
									break
									self.end_message = "Search ended because no more tweets were found."
								maxId = self._search_extension(result)
						except TwitterHTTPError:
							if api_number < len(keys)-1:
								api_number += 1
								api = api_list[api_number]
								continue
							else:
								break
								self.end_message = "Search ended because the Rate Limit was reached."
			#if not howMany_option
			else:
				#iterate until break or rate limit
				cond = True
				maxId = []
				while cond:
					try:
						if counter == 0:
							for query in self.querys:
								result = api.search.tweets(q=query, **params_1)
								if len(result["statuses"]) == 0:
									cond = False
									self.end_message = "Search ended because no more tweets were found."
								maxId.append(self._search_extension(result))
							counter += 1
						#check if until was chosen
						elif self.until:
							for i, query in enumerate(self.querys):
								result = api.search.tweets(q=query, max_id=maxId[i]-1, **params_2)
								if len(result["statuses"]) == 0:
									cond = False
									self.end_message = "Search ended because no more tweets were found."
								maxId[i] = self._search_extension(result)
								if maxId[i] == False:
									cond = False
									self.end_message = "Search ended because Enddate was reached"
						#if until was not chosen
						else:
							for i, query in enumerate(self.querys):
								result = api.search.tweets(q=query, max_id=maxId[i]-1, **params_2)
								if len(result["statuses"]) == 0:
									cond = False
									self.end_message = "Search ended because no more tweets were found."
								maxId[i] = self._search_extension(result)
					except TwitterHTTPError:
						if api_number < len(keys)-1:
							api_number += 1
							api = api_list[api_number]
							continue
						else:
							break
							self.end_message = "Search ended because the Rate Limit was reached."
		#if not search_option
		else:
			if self.howMany_option:
				for x in range(self.howMany):
					try:
						if counter == 0:
							result = api.search.tweets(**params_1)
							if len(result["statuses"]) == 0:
								break
								self.end_message = "Search ended because no more tweets were found."
							maxId = self._search_extension(result)
							counter += 1
						else:
							result = api.search.tweets(max_id=maxId-1, **params_2)
							if len(result["statuses"]) == 0:
								break
								self.end_message = "Search ended because no more tweets were found."
							maxId = self._search_extension(result)
					except TwitterHTTPError:
						if api_number < len(keys)-1:
							api_number += 1
							api = api_list[api_number]
							continue
						else:
							break
							self.end_message = "Search ended because the Rate Limit was reached."
			#if not howMany_option
			else:
				while True:
					try:
						if counter == 0:
							result = api.search.tweets(**params_1)
							if len(result["statuses"]) == 0:
								break
								self.end_message = "Search ended because no more tweets were found."
							maxId = self._search_extension(result)
							counter += 1
						#check if until was chosen
						elif self.until:
							result = api.search.tweets(max_id=maxId-1, **params_2)
							if len(result["statuses"]) == 0:
								break
								self.end_message = "Search ended because no more tweets were found."
							maxId = self._search_extension(result)
							if maxId == False:
								break
								self.end_message = "Search ended because Enddate was reached"
						#if until was not chosen
						else:
							result = api.search.tweets(max_id=maxId-1, **params_2)
							if len(result["statuses"]) == 0:
								break
								self.end_message = "Search ended because no more tweets were found."
							maxId = self._search_extension(result)
					except TwitterHTTPError:
						if api_number < len(keys)-1:
							api_number += 1
							api = api_list[api_number]
							continue
						else:
							break
							self.end_message = "Search ended because the Rate Limit was reached."

		if not self.end_message:
			self.end_message = "Search ended because the samplesize was reached or date limit of the Twitter API was reached."
		if len(self.results_raw) > 0:
			self._sort()
		else:
			self.error = True

	def _search_extension(self, result):
		"""
		This function appends the fetched tweets to self.results_raw. 
		It also checks for each tweet, if it's date is equal to the date in until. If yes, it returns False.
		If not, it returns the maxId for the next search.
		Parameter: result: JSON from Twittter API
		Returns: max_id for next twitter search or False
		"""
		for tweet in result["statuses"]:
			date = parser.parse(tweet["created_at"]).date()
			if date == self.until:
				return False
			self.results_raw.append(tweet)

		maxId = result["statuses"][-1]["id"]
		return maxId

	def _sort(self):
		"""
		This function takes the raw list and sorts the tweets into three seperate lists, depending on the used hashtags.
		Does not return anything. Instead it changes variables in __init__().
		"""
		ids = []
		for tweet in self.results_raw:
			#check if tweet was already here
			if tweet["id"] not in ids:
				ids.append(tweet["id"])
				unique_1 = True
				unique_same = True
				unique_2 = True
				#check if hashtags were used
				if tweet.get("retweeted_status"):
					if tweet["retweeted_status"]["entities"]["hashtags"]:
						for hashtag in tweet["retweeted_status"]["entities"]["hashtags"]:
							self.hashtag_list.append(hashtag["text"])
							if hashtag["text"].casefold() == self.querys[0][1:].casefold():
								if unique_1:
									self.results_1.append(tweet)
									unique_1 = False

							if hashtag["text"].casefold() == self.querys[1][1:].casefold():
								if unique_2:
									self.results_2.append(tweet)
									unique_2 = False

							if unique_1 == False and unique_2 == False:
								if unique_same:
									self.results_same.append(tweet)
									unique_same = False

				elif tweet["entities"]["hashtags"]:
					for hashtag in tweet["entities"]["hashtags"]:
						self.hashtag_list.append(hashtag["text"])
						if hashtag["text"].casefold() == self.querys[0][1:].casefold():
							if unique_1:
								self.results_1.append(tweet)
								unique_1 = False

						if hashtag["text"].casefold() == self.querys[1][1:].casefold():
							if unique_2:
								self.results_2.append(tweet)
								unique_2 = False

						if unique_1 == False and unique_2 == False:
							if unique_same:
								self.results_same.append(tweet)
								unique_same = False
		self.number_of_tweets = str(len(ids))		

	def overview(self):
		"""
		This function calculates basic statistics for all three lists.
		Returns: pandas.dataframe
		"""
		results = [self.results_1, self.results_same, self.results_2]
		length = [len(self.results_1),len(self.results_same),len(self.results_2)]
		links = [[0,0],[0,0],[0,0]]
		replies = [[0,0],[0,0],[0,0]]
		retweets = [[0,0],[0,0],[0,0]]
		hashtags = [[],[],[]]
		text_lenghts = [[],[],[]]
		word_count = [[0,0,0],[0,0,0],[0,0,0]]
		pictures = [[0,0],[0,0],[0,0]]
		user_count_with = [[],[],[]]
		user_count_without = [[],[],[]]
		users_RT = [0,0,0]
		users_without_RT = [0,0,0]

		for i, result in enumerate(results):
			for tweet in result:
				words = []
				string = tweet["full_text"]
				user_count_with[i].append(tweet["user"]["id"])
				user_count_without[i].append(tweet["user"]["id"])

				if tweet["entities"]["urls"]:
					links[i][0] += 1

				if tweet["in_reply_to_user_id"]:
					replies[i][0] += 1

				if tweet.get("retweeted_status"):
					retweets[i][0] += 1
					string = tweet["retweeted_status"]["full_text"]
					user_count_without[i].pop(-1)

				if tweet["entities"]["hashtags"]:
					for hashtag in tweet["entities"]["hashtags"]:
						hashtags[i].append(hashtag["text"])
						
				for word in string.split():
					words.append(word)
				if "http" in words[-1]:
					if len(words) > 1:
						words.pop(-1)
				text_lenghts[i].append(len(words))

				if tweet["entities"].get("media"):
					if tweet["entities"]["media"][0]["type"] == "photo":
						pictures[i][0] += 1

		#count and sort hashtags
		count_hashtags = [[],[],[]]
		for i, hashtag in enumerate(hashtags): 
			for x in set(hashtag):
				count_hashtags[i].append((x, hashtag.count(x), str(round(100/len(hashtag)*hashtag.count(x), 2)) + "%" + " of hashtags"))
		for hashtag in count_hashtags:
			hashtag.sort(key=lambda x:x[1], reverse=True)

		#Calculate percentages
		for i,x in enumerate(links):
			if x[0] > 0:
				x[1] = 100/len(results[i])*x[0]

		for i,x in enumerate(replies):
			if x[0] > 0:
				x[1] = 100/len(results[i])*x[0]

		for i,x in enumerate(retweets):
			if x[0] > 0:
				x[1] = 100/len(results[i])*x[0]

		for i,x in enumerate(pictures):
			if x[0] > 0:
				x[1] = 100/len(results[i])*x[0]

		#count distinct users
		for i,x in enumerate(user_count_with):
			users_RT[i] = len(set(x))
		for i,x in enumerate(user_count_without):
			users_without_RT[i] = len(set(x))

		#Calculate min, max and mean of word counts
		for i, x in enumerate(text_lenghts):
			if len(x) > 1:
				word_count[i][0] = min(x)
				word_count[i][1] = max(x)
				word_count[i][2] = sum(x)/len(x)

		#create a dict
		dic = {
			"query1": {
				"tweets": length[0],
				"distinct_users": [users_RT[0], users_without_RT[0]],
				"retweets": [retweets[0][0], round(retweets[0][1], 1)],
				"replies": [replies[0][0], round(replies[0][1], 1)],
				"links": [links[0][0], round(links[0][1], 1)],
				"photos": [pictures[0][0], round(pictures[0][1], 1)],
				"word_count": [word_count[0][0], word_count[0][1], round(word_count[0][2], 1)]
			},
			"both": {
				"tweets": length[1],
				"distinct_users": [users_RT[1], users_without_RT[1]],
				"retweets": [retweets[1][0], round(retweets[1][1], 1)],
				"replies": [replies[1][0], round(replies[1][1], 1)],
				"links": [links[1][0], round(links[1][1], 1)],
				"photos": [pictures[1][0], round(pictures[1][1], 1)],
				"word_count": [word_count[1][0], word_count[1][1], round(word_count[1][2], 1)]
			},
			"query2": {
				"tweets": length[2],
				"distinct_users": [users_RT[2], users_without_RT[2]],
				"retweets": [retweets[2][0], round(retweets[2][1], 1)],
				"replies": [replies[2][0], round(replies[2][1], 1)],
				"links": [links[2][0], round(links[2][1], 1)],
				"photos": [pictures[2][0], round(pictures[2][1], 1)],
				"word_count": [word_count[2][0], word_count[2][1], round(word_count[2][2], 1)]
			}
		}

		return dic

	def graph(self, filename):
		"""
		This function returns a dictionary with information about the tweets, which will be rendered into graphs.
		Returns: dictionary
		"""
		results = [self.results_1, self.results_same, self.results_2]
		languages = [[],[],[]]
		count_languages = [[],[],[]]
		interfaces = [[],[],[]]
		count_interfaces = [[],[],[]]
		count_interfaces = [[],[],[]]
		co_hashtags = [[],[],[]]
		co_hashtags_sorted = [[],[],[]]
		timeline = [[],[],[]]
		timeline_sorted = [[],[],[]]


		#Get the used items
		for i, result in enumerate(results):
			for tweet in results[i]:
				languages[i].append(tweet["metadata"]["iso_language_code"])
				string = tweet["source"]
				start = string.find(">") + 1
				end = string.find("</")
				interfaces[i].append(string[start:end])
				date = parser.parse(tweet["created_at"])
				timeline[i].append(date.strftime("%Y-%m-%d %H"))

		#Co-hashtags
		for tweet in self.results_1:
			if tweet["entities"]["hashtags"]:
				for hashtag in tweet["entities"]["hashtags"]:
					if hashtag["text"].casefold() != self.querys[0][1:].casefold():
						co_hashtags[0].append(hashtag["text"])

		for tweet in self.results_same:
			if tweet["entities"]["hashtags"]:
				for hashtag in tweet["entities"]["hashtags"]:
					if (hashtag["text"].casefold() != self.querys[0][1:].casefold()) and (hashtag["text"].casefold() != self.querys[1][1:].casefold()):
						co_hashtags[1].append(hashtag["text"])

		for tweet in self.results_2:
			if tweet["entities"]["hashtags"]:
				for hashtag in tweet["entities"]["hashtags"]:
					if hashtag["text"].casefold() != self.querys[1][1:].casefold():
						co_hashtags[2].append(hashtag["text"])

		#count and sort
		#languages
		for i, lang in enumerate(languages):
			for x in set(lang):
				count_languages[i].append((x, lang.count(x), str(round(100/len(results[i])*lang.count(x), 2)) + "%"))
		for lang in count_languages:
			lang.sort(key=lambda x:x[1], reverse=True)
		#interfaces
		for i, inter in enumerate(interfaces):
			for x in set(inter):
				count_interfaces[i].append((x, inter.count(x), str(round(100/len(results[i])*inter.count(x), 2)) + "%"))
		for inter in count_interfaces:
			inter.sort(key=lambda x:x[1], reverse=True)
		#co_hashtags
		for i, hashtag in enumerate(co_hashtags):
			for x in set(hashtag):
				co_hashtags_sorted[i].append((x, hashtag.count(x), str(round(100/len(co_hashtags[i])*hashtag.count(x), 2)) + "%"))
		for hasht in co_hashtags_sorted:
			hasht.sort(key=lambda x:x[1], reverse=True)
		#timeline
		for i, sublist in enumerate(timeline):
			for x in set(sublist):
				timeline_sorted[i].append((x, sublist.count(x)))
		for sublist in timeline_sorted:
			sublist.sort(key=lambda x:x[0])

		#check for missing hours in list
		first_dates = []
		last_dates = []
		for sublist in timeline_sorted:
			if len(sublist) > 0:
				first_dates.append(sublist[0][0])
				last_dates.append(sublist[-1][0])
				for e, item in enumerate(sublist):
					#check if last item in list
					if item == sublist[-1]:
						break
					first_date = datetime.strptime(item[0], "%Y-%m-%d %H")
					next_date = datetime.strptime(sublist[e+1][0], "%Y-%m-%d %H")
					#check for gap
					if first_date + timedelta(hours=1) != next_date:
						new_date = (first_date + timedelta(hours=1)).strftime("%Y-%m-%d %H")
						sublist.insert(e+1, (new_date, 0))		
		#check for first and last date
		for sublist in timeline_sorted:
			if len(sublist) > 0:
				while sublist[0][0] != min(first_dates):
					check_date = datetime.strptime(sublist[0][0], "%Y-%m-%d %H")
					sublist.insert(0, ((check_date - timedelta(hours=1)).strftime("%Y-%m-%d %H"),0))
		for sublist in timeline_sorted:
			if len(sublist) > 0:
				while sublist[-1][0] != max(last_dates):
					check_date = datetime.strptime(sublist[-1][0], "%Y-%m-%d %H")
					sublist.append(((check_date + timedelta(hours=1)).strftime("%Y-%m-%d %H"),0))

		#Create a dictionary
		dic = {
			"languages": {
				"query1": {
					"labels": [x[0] for x in count_languages[0]],
					"values": [x[1] for x in count_languages[0]],
					"percentages": [x[2] for x in count_languages[0]],
				},
				"same": {
					"labels": [x[0] for x in count_languages[1]],
					"values": [x[1] for x in count_languages[1]],
					"percentages": [x[2] for x in count_languages[1]]
				},
				"query2": {
					"labels": [x[0] for x in count_languages[2]],
					"values": [x[1] for x in count_languages[2]],
					"percentages": [x[2] for x in count_languages[2]]
				}
			},
			"interfaces": {
				"query1": {
					"labels": [x[0] for x in count_interfaces[0]],
					"values": [x[1] for x in count_interfaces[0]],
					"percentages": [x[2] for x in count_interfaces[0]],
				},
				"same": {
					"labels": [x[0] for x in count_interfaces[1]],
					"values": [x[1] for x in count_interfaces[1]],
					"percentages": [x[2] for x in count_interfaces[1]],
				},
				"query2": {
					"labels": [x[0] for x in count_interfaces[2]],
					"values": [x[1] for x in count_interfaces[2]],
					"percentages": [x[2] for x in count_interfaces[2]],
				}
			},
			"co_hashtags": {
				"query1": {
					"labels": ["#"+x[0] for x in co_hashtags_sorted[0]],
					"values": [x[1] for x in co_hashtags_sorted[0]],
					"percentages": [x[2] for x in co_hashtags_sorted[0]]
				},
				"same": {
					"labels": ["#"+x[0] for x in co_hashtags_sorted[1]],
					"values": [x[1] for x in co_hashtags_sorted[1]],
					"percentages": [x[2] for x in co_hashtags_sorted[1]]
				},
				"query2": {
					"labels": ["#"+x[0] for x in co_hashtags_sorted[2]],
					"values": [x[1] for x in co_hashtags_sorted[2]],
					"percentages": [x[2] for x in co_hashtags_sorted[2]]
				}
			},
			"timeline": {
				"query1": {
					"data": timeline_sorted[0]
				},
				"same": {
					"data": timeline_sorted[1]
				},
				"query2": {
					"data": timeline_sorted[2]
				}
			}
		}

		with open("static/json/"+filename, "w") as file:
			json.dump(dic, file)
		return dic

	def tweets_to_df(self):
		"""
		This function returns a table of all tweets.
		Returns: pandas.dataframe
		"""
		df1 = json_normalize(self.results_1)
		df1["hashtag"] = self.querys[0]
		df_same = json_normalize(self.results_same)
		df_same["hashtag"] = "both"
		df2 = json_normalize(self.results_2)
		df2["hashtag"] = self.querys[1]

		df_all = df1.append((df_same, df2), ignore_index=True)
		return df_all

	def create_gexf_data(self, filename):
		"""
		This function manages the data to be ready for _create_gexf.
		Parameter: filename: string
		"""
		hashtags = list(set(self.hashtag_list))
		gexf_list = []

		for hashtag in hashtags:
			gexf_list.append({"id":hashtags.index(hashtag), "name": "#" + hashtag, "value": self.hashtag_list.count(hashtag), "edges": []})

		ids = []
		for tweet in self.results_raw:
			if tweet["id"] not in ids:
				ids.append(tweet["id"])
				if tweet.get("retweeted_status"):
					if tweet["retweeted_status"]["entities"]["hashtags"]:
						used_hashtags = [x["text"] for x in tweet["retweeted_status"]["entities"]["hashtags"]]
						for hashtag in used_hashtags:
							index = hashtags.index(hashtag)
							for element in used_hashtags:
								if element != hashtag:
									gexf_list[index]["edges"].append(element)
				else:
					if tweet["entities"]["hashtags"]:
						used_hashtags = [x["text"] for x in tweet["entities"]["hashtags"]]
						for hashtag in used_hashtags:
							index = hashtags.index(hashtag)
							for element in used_hashtags:
								if element != hashtag:
									gexf_list[index]["edges"].append(element)

		for item in gexf_list:
			new_edges = []
			for element in set(item["edges"]):
				new_edges.append((hashtags.index(element), element, item["edges"].count(element)))
			item["edges"] = new_edges

		_create_gexf(gexf_list, filename)

def _create_gexf(data, filename):
	"""
	This function creates a gexf.file from the data it receives.
	"""
	gexf = etree.Element("gexf", version= "1.3")
	graph = etree.SubElement(gexf, "graph", defaultedgetype= "undirected", mode= "static")
	attributes = etree.SubElement(graph, "attributes", {"class": "node", "mode": "static"})

	etree.SubElement(attributes, "attribute", {"id": "frequency", "title": "frequency", "type": "integer"})
	etree.SubElement(attributes, "attribute", {"id": "number_of_edges", "title": "number_of_edges", "type": "integer"})

	nodes = etree.SubElement(graph, "nodes")
	edges = etree.SubElement(graph, "edges")

	for item in data:
		node = etree.SubElement(nodes, "node", id= str(item["id"]), Label= item["name"])
		attvalues = etree.SubElement(node, "attvalues")

		etree.SubElement(attvalues, "attvalue", {"for": "frequency", "value": str(item["value"])})
		etree.SubElement(attvalues, "attvalue", {"for": "number_of_edges", "value": str(len(item["edges"]))})

		for connection in item["edges"]:
			etree.SubElement(edges, "edge", {"id": str(item["id"])+"_"+str(connection[0]), "source": str(item["id"]), "target": str(connection[0]), 
							"weight": str(connection[2]/2)})

	with open("static/downloads/"+filename, "w", encoding="utf-8") as file:
		file.write(etree.tostring(gexf, encoding="utf-8", method="xml").decode("utf-8"))

def api_status():
	"""
	This function returns the remaining searches of the API key and the reset time..
	Returns: list: 2 values 
	first: integer: remaining searches 
	second: string: reset time
	"""
	rate_limit_status = []
	status = []	
	for i, api in enumerate(api_list):
		rate_limit_status.append(api.application.rate_limit_status())
		reset = rate_limit_status[i]["resources"]["search"]["/search/tweets"]["reset"]
		status.append(((rate_limit_status[i]['resources']['search']['/search/tweets']["remaining"]), time.strftime("%H:%M:%S", time.localtime(reset))))
	return status