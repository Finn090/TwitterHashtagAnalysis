# TwitterHashtagAnalysis
Python based tool for analysing the use of hashtags on twitter.

This tool launches a flask instance which you can find at ```localhost:5000``` in your Browser. There you can make various inputs but most importantly you need to give two hashtags to compare. The tool then searches for tweets containing the hashtags using the Twitter API. It then creates a bunch of graphs a tables to enable the user to get an overview of the usage of these hashtags. Also you an download all tweets in a csv-file. 

The feature I am most proud of is the generation of a network file (gexf). You can also download this in the web interface. For this network the tool looks at all hashtags and creates a node for each. If two hashtags are present in the same tweet, an edge is created between the two nodes and every other time both hashtags are present in a tweet, the strength of that edge is increased by 1.

## How to install

 - Clone this repository
 - Install the needed modules specified in requirements.txt using ```pip install -r requirements.txt```
 - Put your Twitter API keys into the variable ```keys``` in line 11 of twTool.py. If you have multiple keys, create multiple dictionaries inside the list. The tool can handle multiple keys.
 - Run the flask_app.py using the command ```python flask_app.py```
 - Go to ```localhost:5000``` in your Browser
