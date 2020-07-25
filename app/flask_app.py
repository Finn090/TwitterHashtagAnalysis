from flask import Flask, render_template, request, session, redirect, url_for, abort
import twTool
import pandas as pd
import datetime
from dateutil import parser
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = b'_0#e5L"F4k8zn6xeJ]/'

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
			if since or until or howMany:
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
								return render_template("home.html", error=error, date1=since, date2=until)

						else:
							session["until"] = until
					else:
						error = "The date for the end of the sample is incorrect. The Twitter API only allows searches in the past 7 days, not any further. Also you cannot pick dates from the future."
						return render_template("home.html", error=error, date1=until)
				else:
					session.pop("until", None)
			else:
				error = "At least one option for limiting the search must be checked. If you don't want to limit anything, check the startdate and choose today."
				return render_template("home.html", error=error)

			#make sure hashtags are used
			if query1[0] != "#":
				query1 = "#" + query1
			if query2[0] != "#":
				query2 = "#" + query2

			#check if howMany is given
			if howMany_option:
				session["howMany"] = int(howMany)
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
			return render_template("home.html", error=error)

	return render_template("home.html", status=status)

@app.route("/htool")
def htool():
	"""
	This page is the results screen of the tool.
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
		
		df = outcome.overview()
		#Convert tables to html code
		html_table_1 = df[[session.get("query1")]].to_html()
		html_table_same = df[["tweets with both hashtags"]].to_html()
		html_table_2 = df[[session.get("query2")]].to_html()
	
		dic = outcome.graph()
		#languages legends
		lang_legends = [
			str(session.get("query1")) + " , languages, top 5",
			"both hashtags" + ", languages, top 5",
			str(session.get("query2")) + " , languages, top 5"]

		#interface legends
		inter_legends = [
			str(session.get("query1")) + " , interfaces, top 5",
			"both hashtags" + " , interfaces, top 5",
			str(session.get("query2")) + " , interfaces, top 5"]

		#co-hashtag legends
		co_legends = [
		str(session.get("query1")) + " , Co-hashtags, top 10",
		"both hashtags" + " , Co-hashtags, top 10",
		str(session.get("query2")) + " , Co-hashtags, top 10"]

		#timeline legends
		timeline_legends = [str(session.get("query1")), "both hashtags" ,str(session.get("query2"))]

		#create search_parameters for website
		search_parameters = [session.get("query1"), session.get("query2"), since, until, howMany, session.get("search_option"), len(outcome.results_raw)]

		#csv download
		df = outcome.tweets_to_df()
		#filename
		csv_name = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
		query1 = session.get("query1")[1:]
		query2 = session.get("query2")[1:]
		csv_filename = f"THA-{csv_name}-{query1}-{query2}.csv"
		#folder
		outpath = os.path.join('static', 'downloads')
		if not os.path.isdir(outpath):
			os.makedirs(outpath)
		#download link
		csv_download_link = os.path.join(outpath, csv_filename)
		#csv_download_link = Markup(f'<p><a href="{csv_download_link}">Download results.</a></p>')
		#create csv
		df.to_csv(csv_download_link, sep=";")

		return render_template("htool.html",
			table_1=html_table_1, table_same=html_table_same, table_2=html_table_2,
			lang_legends=lang_legends, inter_legends=inter_legends, co_legends=co_legends, timeline_legends=timeline_legends,
			dic=dic, search_parameters=search_parameters, csv_download_link=csv_download_link)

@app.route("/about")
def about():
	return render_template("about.html")

@app.route("/datenschutz")
def datenschutz():
	return render_template("datenschutz.html")

@app.errorhandler(409)
def rate_limit_exceeded(error):
	status = twTool.api_status()
	return render_template("error.html", status=status), 409

if __name__ == "__main__":
	app.run(debug=True)