#!c:/Python27/python.exe -u

# Hamilton Restaurant Food Safety Inspection Scraper
# Scrapes the inspection data from http://www.foodsafetyzone.ca
# Then outputs the JSON representation.
#
# @author: Gavin Schulz <gavin.schulz@gmail.com>

### History ###
# 4/11/2011 - First version of scraper

import requests, re, time
import simplejson as json
from threading import Thread
from BeautifulSoup import BeautifulSoup

# Scrape a inspection detail page and returns 
# a BeautifulSoup instance
def getDetails(premise, date, inspectionID):
	_q = {'SelectedPremise': premise, 'SelectedDate': date, 'InspectionID': inspectionID}
	r = requests.post('http://www.foodsafetyzone.ca/zonedetails3.asp', data = _q)

	return BeautifulSoup(r.content)

def processInspection(info, restaurant, date, inspectionID):
	details = {"infractions": [], "actions": [], "date": date, "inspectionID": inspectionID}
	x = 0

	while x < len(info):
		try:
			if re.search(r'\bInspection\sdate', info[x].string):
				x = x + 1
				details["date"] = info[x].li.string.strip()
			elif re.search(r'\bInspection\stype', info[x].string):
				x = x + 1
				details["type"] = info[x].li.string.strip()
			elif re.search(r'\bMinor\sInfractions', info[x].string):
				x = x + 1

				# This is a ul where each li contains one infraction
				for i in info[x]:
					li = ''
					try:
						for z in i.contents:
							li = li + z.string.strip()
					except:
						li = i.string.strip()
					if len(li.strip()) > 0:
						details["infractions"].append({"type": "minor", "content": li.strip()})
			elif re.search(r'\bCritical\sInfractions', info[x].string):
				x = x + 1

				# This is a ul where each li contains one infraction
				for i in info[x]:
					li = ''
					try:
						for z in i.contents:
							li = li + z.string.strip()
					except:
						li = i.string.strip()
					if len(li.strip()) > 0:
						details["infractions"].append({"type": "critical", "content": li.strip()})
			elif re.search(r'\bActions\staken', info[x].string):
				x = x + 1

				# This is a ul where each li contains one action
				for i in info[x]:
					li = ''
					try:
						for z in i.contents:
							li = li + z.string.strip()
					except:
						li = i.string.strip()
					if len(li.strip()) > 0:
						details["actions"].append({"content": li.strip()})

		except Exception, err:
			print str(err)
			# Didn't match anything we'll, let it slip
			print "Could not match: \"" + str(info[x]) + "\""

		x = x + 1

	restaurant["inspections"].append(details)

# Scrapes all inspection data for a restaurant
# ``restaurant`` is an instance of the Restaurant class
# Returns the fully-fleshed out Restaurant object
def processRestaurant(restaurant):
	_soup = getDetails(restaurant["premise"], restaurant["date"], restaurant["inspectionID"])
	place = _soup.h5.string.strip().split(',')

	# Flesh out basic restaurant details
	restaurant["name"] = _soup.h1.string.strip()
	restaurant["address"] = place[0].strip()
	restaurant["neighbourhood"] = place[1].strip()

	info = _soup(['h4', 'ul'])

	processInspection(_soup(['h4', 'ul']), restaurant, restaurant["date"], restaurant["inspectionID"])
	
	print "Processing inspections for " + restaurant["premise"]

	# Find the other inspection reports available
	for report in _soup('tr'):
		try:
			linkProp = report.td.a["href"]
			linkProp = linkProp[(linkProp.find('(') + 1):linkProp.find(')')].split(',')

			__soup = getDetails(restaurant["premise"], linkProp[0].strip().strip("'"), linkProp[1].strip().strip("'"))
			info = __soup(['h4', 'ul'])

			processInspection(__soup(['h4', 'ul']), restaurant, linkProp[0].strip().strip("'"), linkProp[1].strip().strip("'"))
		except:
			# This is the currently displayed inspection report
			# so we just skip over it
			pass

def processPage(restaurants, page):
	print "Processing page: " + str(page)

	for x in restaurants:
		processRestaurant(x)
		del x['inspectionID']
		del x['date']
	
	f = open('results/11_5_2011_' + str(page - 1) + '.json', 'w')
	f.write(json.dumps(restaurants, sort_keys=True))
	f.close()



print "####################################"
print "# Scraping data. . . . . "

restaurants = []

print "# Scraping search result pages"
for X in range(20, 31):
	# Makes a request to the main search interface
	# ``X`` is the page number to scrape
	print "Fetching http://www.foodsafetyzone.ca/zonesearch3.asp with X = " + str(X)
	r = requests.post('http://www.foodsafetyzone.ca/zonesearch3.asp', data={'X': X})

	soup = BeautifulSoup(r.content)
	restaurants.append([])
	i = 0

	# Find all the inspection results on this page
	for x in soup('tr', bgcolor=lambda(x): x == "white" or x == "whitesmoke"):
		# Get the result properties
		linkProp = x.td.b.a["href"]
		linkProp = linkProp[(linkProp.find('(') + 1):linkProp.find(')')].split(',')

		# Create new Restaurant object and set properties
		_r = {}
		_r["inspections"]  = []
		_r["premise"]      = linkProp[0].strip().strip("'")
		_r["date"]         = linkProp[1].strip().strip("'")
		_r["inspectionID"] = linkProp[2].strip().strip("'")
		restaurants[(X - 19) - 1].append(_r)

		i = i + 1
	
	print "Found " + str(i) + " records."

	try:
		Thread(target=processPage, args=(restaurants[(X - 19) - 1], X)).start()
	except Exception, err:
		print err