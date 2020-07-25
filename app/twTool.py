from twitter import Twitter, OAuth, TwitterHTTPError
import time
from datetime import datetime, timedelta
import pandas as pd
import re
from dateutil import parser

token = "878227804063707136-Ez3Z4a2xSTIoTv1qZqwHJTJMGa6jPQV"
token_secret = "8wf0mK8wAm8SJ0yFu5Kphkots6N2TZChlo5jPtcimA9qx"
consumer_key = "x0XwdSNePCkYaqirJWZv3rlOF"
consumer_secret = "NIH4AO82E0tD28yB1gi6llQ9wwYsJf3mdMzDClwzsthce63FOY"
api = Twitter(auth = OAuth(token, token_secret, consumer_key, consumer_secret))

class twTool():
	"""
	This Tool compares the tweets of two different hashtags and the tweets which use both hashtags.
	It gets tweets via two Twitter API searches, one for each hashtag. 
	It then takes the data of the two lists of tweets and calculates, hopefully interesting, statistics out of it.
	The class has two mandatory parameters and an optional one. The first two are the two hashtags,
	which are needed as querys for the Twitter API search. 
	The third one is an integer and tells the class how many iterations of each search it should make. 
	One iteration yields up to 100 tweets.
	"""
	def __init__(self, query1: str, query2: str, since=False, until=False, howMany: int=0, search_option=False):
		self.querys = []
		#make sure querys will be hashtags
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
		self.howMany = howMany

		self.search_option = search_option

		self.results_raw = []
		self.results_1 = []
		self.results_2 = []
		self.results_same = []

		self.error = False
		self._search()

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

	def _search(self):
		"""
		This function carries out the Twitter search via the Twitter API.
		The logic of the search is determined by the parameters with which the class is called.
		It calls _sort() when it's finished.
		"""
		#search parameters
		params_1 = dict(include_entities=True, tweet_mode="extended", result_type="recent", count=100)
		params_2 = dict(include_entities=True, tweet_mode="extended", result_type="recent", count=100)
		if self.since:
			params_1["until"] = self.since
		if not self.search_option:
			params_1["q"] = self.querys[0]+" OR "+self.querys[1]
			params_2["q"] = self.querys[0]+" OR "+self.querys[1]

		results_raw = []
		try:
			#check for search_option
			if self.search_option:				
				#check for howMany
				if self.howMany_option:
					#check for each query
					for query in self.querys:
						#for chosen sample size
						for x in range(0, self.howMany):
							#first search with since
							if x == 0:
								result = api.search.tweets(q=query, **params_1)
								#check for 0 results
								if len(result["statuses"]) == 0:
									break
									print("0 results")
								maxId = self._search_extension(result)
							#all following searches
							else:
								result = api.search.tweets(q=query, max_id=maxId-1, **params_2)
								if len(result["statuses"]) == 0:
									break
									print("0 results")
								maxId = self._search_extension(result)
				#if not howMany_option
				else:
					#iterate until break or rate limit
					counter = 0
					cond = True
					maxId = []
					while cond:
						if counter == 0:
							for query in self.querys:
								result = api.search.tweets(q=query, **params_1)
								if len(result["statuses"]) == 0:
									cond = False
									print("0 results")
								maxId.append(self._search_extension(result))
								counter += 1
						#check if until was chosen
						elif self.until:
							for i, query in enumerate(self.querys):
								result = api.search.tweets(q=query, max_id=maxId[i], **params_2)
								if len(result["statuses"]) == 0:
									cond = False
									print("0 results")
								maxId[i] = self._search_extension(result)
								if maxId[i] == False:
									cond = False
									print("date ended")
						#if until was not chosen
						else:
							for i, query in enumerate(self.querys):
								result = api.search.tweets(q=query, max_id=maxId[i], **params_2)
								if len(result["statuses"]) == 0:
									cond = False
									print("0 results")
								maxId[i] = self._search_extension(result)
			#if not search_option
			else:
				if self.howMany_option:
					for x in range(0, self.howMany):
						if x == 0:
							result = api.search.tweets(**params_1)
							if len(result["statuses"]) == 0:
								break
								print("0 results")
							maxId = self._search_extension(result)
						else:
							result = api.search.tweets(max_id=maxId-1, **params_2)
							if len(result["statuses"]) == 0:
								break
								print("0 results")
							maxId = self._search_extension(result)
				#if not howMany_option
				else:
					counter = 0
					while True:
						if counter == 0:
							result = api.search.tweets(**params_1)
							if len(result["statuses"]) == 0:
								break
								print("0 results")
							maxId = self._search_extension(result)
							counter += 1
						#check if until was chosen
						elif self.until:
							result = api.search.tweets(max_id=maxId-1, **params_2)
							if len(result["statuses"]) == 0:
								break
								print("0 results")
							maxId = self._search_extension(result)
							if maxId == False:
								break
								print("date ended")
						#if until was not chosen
						else:
							result = api.search.tweets(max_id=maxId-1, **params_2)
							if len(result["statuses"]) == 0:
								break
								print("0 results")
							maxId = self._search_extension(result)

		#if error gets raised
		except TwitterHTTPError:
			print("Rate limit reached")
		#output
		finally:
			if len(self.results_raw) > 0:
				self._sort()
			else:
				self.error = True

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
				unique_2 = True
				unique_same = True
				#check if hashtags were used
				if tweet.get("retweeted_status"):
					if tweet["retweeted_status"]["entities"]["hashtags"]:
						for hashtag in tweet["retweeted_status"]["entities"]["hashtags"]:
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
		print(len(ids))				

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
		text_overview = [[0,0,0],[0,0,0],[0,0,0]]
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
				text_overview[i][0] = min(x)
				text_overview[i][1] = max(x)
				text_overview[i][2] = sum(x)/len(x)

		#Create a dataframe
		df = pd.DataFrame(columns=[self.querys[0], "tweets with both hashtags", self.querys[1]])
		for i,col in enumerate(df):
			df.loc["number of tweets", col] = length[i]
			df.loc["tweets with links", col] = str(links[i][0]) + ", " + str(round(links[i][1], 2)) + "%" + " of tweets"
			df.loc["tweets as replies", col] = str(replies[i][0]) + ", " + str(round(replies[i][1], 2)) + "%" + " of tweets"
			df.loc["tweets as retweets", col] = str(retweets[i][0]) + ", " + str(round(retweets[i][1], 2)) + "%" + " of tweets"
			df.loc["word count: min, max and mean", col] = str(text_overview[i][0]) + ", " + str(text_overview[i][1]) + ", " + str(round(text_overview[i][2], 2))
			df.loc["tweets with photos", col] = str(pictures[i][0]) + ", " + str(round(pictures[i][1], 2)) + "%" + " of tweets"
			df.loc["distinct users", col] = str(users_RT[i]) + ", " + str(users_without_RT[i])

		return df

	def graph(self):
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
			while sublist[0][0] != min(first_dates):
				check_date = datetime.strptime(sublist[0][0], "%Y-%m-%d %H")
				sublist.insert(0, ((check_date - timedelta(hours=1)).strftime("%Y-%m-%d %H"),0))
		for sublist in timeline_sorted:
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
					"labels": [x[0] for x in co_hashtags_sorted[0]],
					"values": [x[1] for x in co_hashtags_sorted[0]],
					"percentages": [x[2] for x in co_hashtags_sorted[0]]
				},
				"same": {
					"labels": [x[0] for x in co_hashtags_sorted[1]],
					"values": [x[1] for x in co_hashtags_sorted[1]],
					"percentages": [x[2] for x in co_hashtags_sorted[1]]
				},
				"query2": {
					"labels": [x[0] for x in co_hashtags_sorted[2]],
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
		return dic

def api_status():
	"""
	This function returns the remaining searches of the API key and the reset time..
	Returns: list: 2 values 
	first: integer: remaining searches 
	second: string: reset time
	"""
	status = []
	rate_limit_status = api.application.rate_limit_status()
	status.append(rate_limit_status['resources']['search']['/search/tweets']["remaining"])
	reset = rate_limit_status["resources"]["search"]["/search/tweets"]["reset"]
	status.append(time.strftime("%H:%M:%S", time.localtime(reset)))
	return status