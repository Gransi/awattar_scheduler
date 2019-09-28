#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "Peter Gransdorfer"
__copyright__ = "Copyright 2019"

__license__ = "GPL"
__maintainer__ = "Peter Gransdorfer"
__email__ = "peter.gransdorfer[AT]cattronix[com]"

import requests
import http.client
import urllib.parse
import json
import os
import re
import sys
import getopt
import datetime
import dateutil
import configparser
import math
from string import Template
from datetime import timezone
from dateutil import tz
from datetime import timedelta

from influxdb import InfluxDBClient

data = None
config = None

def checkNumericInput(name, value):
	"""
    Check input value and return only numeric value

    Parameters
    ----------
    name : string
        Name of value
    value : string
        Input value

    Returns
    -------
    int
        Returns input value

    """

	if value == None:
		print(name,'is not set')
		sys.exit(2)
	
	try:
		return int(value)
	except ValueError:
		#Handle the exception
		print ('Please enter an numeric for value', name)	
		sys.exit(2)


def getDataFromServer():
	"""
    Get the market data from API of the next day

    Returns
    -------
    int
        Returns the response from the API

    """
	global config

	try:
		
	    #Header for request
		headers = {
			'Authorization': 'Basic ' + config['General']['Authorization']
		}  
		
		#set start timestamp
		starttime = datetime.datetime.now(tz=timezone.utc)
		starttime = starttime.replace(hour=0, minute=0, second=0)	
		starttimestamp = str(int(starttime.timestamp()))
		
		#set end timestamp
		endtime = starttime + datetime.timedelta(days=2)
		endtimestamp = str(int(endtime.timestamp()))
		
		req = requests.get('https://api.awattar.com/v1/marketdata?start=' + starttimestamp + '000&end=' + endtimestamp + '000',headers = headers)
		
		if req.status_code != requests.codes.ok: return 0
		
		return req.json()
	
	except Exception as e:
		print(str(e))
		return 0

def writeDataToInfluxDB():
	"""
    Write data from to InfluDB

    """
	global data
	global config

	client = InfluxDBClient(
		config['InfluxDB']['Server'],
		config['InfluxDB']['Port'],
		config['InfluxDB']['Username'],
		config['InfluxDB']['Password'],
		config['InfluxDB']['Database'])

	#get each json item
	for item in data:
	
		valuestarttime = item['start_timestamp']
		valueprice = item['marketprice']
		
		valuestarttime = valuestarttime / 1000 #remove milliseconds
				
		json_body = [{
				"measurement": "Energy marketprice",
				"time": datetime.datetime.utcfromtimestamp(valuestarttime).isoformat() + 'Z',
				"fields": {
					"value": float(valueprice)
				}
			}]
			
		result = client.write_points(json_body,protocol=u'json',time_precision='s')
		
def searchBestStartingPoint(starttime, periode, duration):
	"""
    Search the best starting point.

    Parameters
    ----------
    starttime : int
        Start time [hour]
    periode : int
        Time range [hour]
	duration : int
		Duration of usage[hour]

    Returns
    -------
    int
        Returns the best starting point

    """

	lowestprice = 99999.0
	lowestpricetime = None
	startatindex = None
	durationround = math.ceil(duration)
	datalenght = len(data) - (durationround - 1)

	#get each json item
	for i in range(0,datalenght):
	
		item = data[i]		
		#get values from response
		valuestarttime = item['start_timestamp']
		valueprice = item['marketprice']
		
		valuestarttime = datetime.datetime.utcfromtimestamp(valuestarttime / 1000).replace(tzinfo=timezone.utc)
		valuestarttime = valuestarttime.astimezone(tz.tzlocal())

		if valuestarttime.hour >= starttime:
			
			if startatindex == None:
				startatindex = i
				
			rangesum = 0
			
			for x in range(0, durationround):
				xtime = datetime.datetime.utcfromtimestamp(data[i+x]['start_timestamp'] / 1000)
				rangesum += data[i+x]['marketprice']
			
			averageprice = rangesum / durationround
			
			if averageprice < lowestprice:
				lowestprice = averageprice
				lowestpricetime = valuestarttime
		
		#Loop finished
		if startatindex != None:
			if i >= (startatindex + (periode-1)):
				break

	print('Best starting point at {:%d.%m.%Y %H:%M} ({:6.4f} EURO)'.format(lowestpricetime, lowestprice/1000))

	return lowestpricetime

def parseConfig():
	"""
    Read config file and parse all Task sections

    """	
	global config
	global data

	#delete output files
	for section in config.sections():
		if 'Task' in section:
			if os.path.isfile(config.get(section, 'output')):
				os.remove(config.get(section, 'output'))

	#write data to InfluxDB
	if config['InfluxDB']['enable']:
		writeDataToInfluxDB()
	
	#searchBestStartingPoint(starttime, periode, duration)
	
	for section in config.sections():

		#process only section with contains 'Task'
		if 'Task' in section:
			if config.getboolean(section, 'enable'):

				#get best start time 
				starttime = searchBestStartingPoint(config.getint(section, 'Starttime'),config.getint(section, 'Periode'),config.getfloat(section, 'Duration'))
				endtime = starttime + timedelta(minutes=60*config.getfloat(section, 'Duration'))

				#write start and end time to output
				templatefile = open(config.get(section, 'Template'))
				src = Template(templatefile.read())
				d={ 'Starttime':starttime.strftime(config.get(section, 'Starttimepattern')), 'Endtime':endtime.strftime(config.get(section, 'Endtimepattern')) }
				outputfile = open(config.get(section, 'Output'),'w')
				outputfile.write(src.substitute(d))
				outputfile.close()				

		
def main(argv):
	"""
    Main routine

    """	
	global config
	global data
	
	config = configparser.ConfigParser()
	config.read('/etc/awattar_scheduler/awattar_scheduler.conf')
 
	
	starttime = None
	periode = None
	duration = None
	
	try:
		opts, args = getopt.getopt(argv,"h",["starttime=","periode=","duration="])
	except getopt.GetoptError:
		print('awattar_cron.py --starttime=<hour> --periode=<hour> --duration=<hour>')
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			print('awattar_cron.py --starttime=<hour> --periode=<hour> --duration=<hour>')
			sys.exit()
		elif opt in ("--starttime"):
			starttime = arg
		elif opt in ("--periode"):
			periode = arg
		elif opt in ("--duration"):
			duration = arg

	if len(opts) == 3:
	#Check inputs
		starttime = checkNumericInput('Starttime', starttime)
		periode = checkNumericInput('Period', periode)
		duration = checkNumericInput('Duration', duration)

	out = getDataFromServer()

	#return if response is empty
	if out == 0:
		print('Can''t download data from server') 
		return
	
	data = out['data']

	if len(opts) == 3:
		searchBestStartingPoint(starttime, periode, duration)
	else:
		parseConfig()


if __name__ == "__main__":
	main(sys.argv[1:])