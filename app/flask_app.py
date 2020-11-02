from flask import Flask, render_template, request, session, redirect, url_for, abort
import twTool
import pandas as pd
import datetime
from dateutil import parser
from datetime import timedelta
import os
import json

app = Flask(__name__)
app.secret_key = b'_0#e5L"F4sk8Zn6xeJ]/'


@app.route("/", methods=["GET"])
def home():
	"""
	This page acts as the front page of the tool and the inputs are made here. 
	"""
	#call api_status() for remaining searches and reset time
	status = twTool.api_status()
	if request.method == "GET":
		query1 = request.args.get("query1", "")
		query2 = request.args.get("query2", "")

		since_option = request.args.get("time_option1", "")
		since = request.args.get("since", "")
		until_option = request.args.get("time_option2", "")
		until = request.args.get("until", "")

		howMany_option = request.args.get("howMany_option")
		howMany = request.args.get("howMany", "")

		search_option = request.args.get("search_option", "")

		if query1 and query2:
			now = datetime.date.today()
			#check if since was chosen
			if since_option:
				#check for correct time chosen
				since = parser.parse(since).date()
				if (now - since) <= timedelta(days=7) and (now - since) >= timedelta(days=0):
					session["since"] = since
				else:
					error = "The date for the start of the sample is incorrect. The Twitter API only allows searches in the past 7 days, not any further. Also you cannot pick dates from the future."
					return render_template("home.html", error=error, date1=since)
			else:
				session.pop("since", None)
			#check if until was chosen
			if until_option:
				#check for correct time chosen
				until = parser.parse(until).date()
				if (until - now) <= timedelta(days=7) and (now - until) >= timedelta(days=0):
					if since_option:
						if (since - until) >= timedelta(days=1):
							session["until"] = until
						else:
							error = "The start of the search must be a later date than the end of the search. The tool collects tweets going backwards in time."
							return render_template("home.html", error=error, date1=since, date2=until, status=status)

					else:
						session["until"] = until
				else:
					error = "The date for the end of the sample is incorrect. The Twitter API only allows searches in the past 7 days, not any further. Also you cannot pick dates from the future."
					return render_template("home.html", error=error, date1=until, status=status)
			else:
				session.pop("until", None)

			#make sure hashtags are used
			if query1[0] != "#":
				query1 = "#" + query1
			if query2[0] != "#":
				query2 = "#" + query2

			#check if howMany is given
			if howMany_option:
				howMany = int(howMany) if howMany else 100
				session["howMany"] = howMany if howMany > 100 else 100
			else:
				session.pop("howMany", None)
			#create session variables
			session["query1"] = query1
			session["query2"] = query2
			#check for cearch_option
			if search_option == "True":
				session["search_option"] = True
			else:
				session["search_option"] = False

			return redirect(url_for("htool"))

		elif query1 or query2 or since or until or howMany:
			error = "Not all necessary fields were filled out."
			return render_template("home.html", error=error, status=status)

	return render_template("home.html", status=status)

@app.route("/htool")
def htool():
	"""
	This page acts as the results screen of the tool.
	"""
	if "query1" and "query2" in session:
		#create variables for search_parameter
		since = None
		until = None
		howMany = None
		#create dict for class call and check for options
		params = dict(query1=session.get("query1"), query2=session.get("query2"), search_option=session.get("search_option"))
		
		if "since" in session:
			params["since"] = session.get("since")
			since = session.get("since")
		if "until" in session:
			params["until"] = session.get("until")
			until = session.get("until")
		if "howMany" in session:
			params["howMany"] = session.get("howMany")
			howMany = session.get("howMany")
			
		outcome = twTool.twTool(**params)
		#check for error	
		if outcome.error == True:
			abort(409)

		#individual json filename
		time_name = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
		query1 = session.get("query1")[1:]
		query2 = session.get("query2")[1:]

		json_filename = f"THA-{time_name}-{query1}-{query2}.json"
		session["json_filename"] = json_filename
		dic = outcome.graph(json_filename)

		#languages legends
		lang_legends = [
			"Top 5 Languages for: " + str(session.get("query1")),
			"Top 5 Languages",
			"Top 5 Languages for: " + str(session.get("query2"))]

		#interface legends
		inter_legends = [
			"Top 10 Interfaces for: " + str(session.get("query1")),
			"Top 10 interfaces",
			"Top 10 interfaces for: " + str(session.get("query2"))]

		#co-hashtag legends
		co_legends = [
			"Top 10 Co-Hashtags for: " + str(session.get("query1")),
			"Top 10 Co-Hashtags",
			"Top 10 Co-Hashtags for: " + str(session.get("query2"))]

		#timeline legends
		timeline_legends = [str(session.get("query1")), "both hashtags" ,str(session.get("query2"))]

		#create search_parameters for website
		search_parameters = [session.get("query1"), session.get("query2"), since, until, howMany, session.get("search_option"),
							outcome.number_of_tweets, outcome.end_message]

		#csv download
		df = outcome.tweets_to_df()
		csv_filename = f"THA-{time_name}-{query1}-{query2}.csv"

		outpath = os.path.join('static', 'downloads')
		if not os.path.isdir(outpath):
			os.makedirs(outpath)
		csv_download_link = os.path.join(outpath, csv_filename)

		df.to_csv(csv_download_link, sep=";")

		#gexf download
		gexf_filename = f"THA-{time_name}-{query1}-{query2}.gexf"
		gexf_download_link = os.path.join(outpath, gexf_filename)
		outcome.create_gexf_data(gexf_filename)

		return render_template("htool.html",
			tables=outcome.overview(),
			lang_legends=lang_legends, inter_legends=inter_legends, co_legends=co_legends, timeline_legends=timeline_legends,
			dic=dic, search_parameters=search_parameters, csv_download_link=csv_download_link, gexf_download_link=gexf_download_link)
	else:
		return """<p>This site does not exist<p>"""

@app.route("/complete_lists")
def complete_lists():
	if "json_filename" and "query1" and "query2" in session:
		count = 0
		df_list = []
		name_list = [session.get("query1"), "both hashtags", session.get("query2")]
		with open("static/json/"+session.get("json_filename")) as file:
			dic = json.load(file)
		for topic in dic:
			if topic != "timeline":
				for x, query in enumerate(dic[topic]):
					df = pd.DataFrame()
					for kind in dic[topic][query]:
						for j, ele in enumerate(dic[topic][query][kind]):
							df.loc[j, kind] = ele
					df = df.to_html(index=False)
					df_list.append((df, topic, name_list[x], count))
					count += 1

		return render_template("complete_lists.html", tables=df_list)

	return render_template("complete_lists.html")

@app.errorhandler(409)
def rate_limit_exceeded(error):
	status = twTool.api_status()
	return render_template("error.html", status=status), 409

if __name__ == "__main__":
	app.run(debug=True, use_reloader=True)