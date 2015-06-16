import json
import requests

from keys import *



def run_query(search_terms):

	# for adding quotes around the search term as required by Bing search API.
	query = "'%s'" % search_terms

	# Creating dict for parameters to pass in the url
	parameters = {'Query': query, '$format': 'JSON', '$top': '10', '$skip' : '0'}

	search_url = 'https://api.datamarket.azure.com/Bing/Search/v1/Web'
	
	# Getting the response by building the url with parameters and authentication.	
	r = requests.get(search_url, params=parameters, auth=('', BING_API_KEY))

	# Convert response to JSON
	p = r.json()

	# Creating our own list for storing the results
	search_results = []


	# Loop for grabbing and storing.
	for item in p['d']['results'] :
		search_results.append({
			'title': item['Title'],
			'link' : item['Url'],
			'summary': item['Description']
			})

	return search_results

## Just for testing the function in the builder
# query1 = 'Django'
# run_query(query1)


## SPECIAL ## 
# The codes below allows to run the program as a standalone application from the command line
# Run python bing_search.py , Neat! 

def main():
	user_input = raw_input("Enter your Search: ")
	run_query(user_input)


if __name__ == '__main__':
	main()