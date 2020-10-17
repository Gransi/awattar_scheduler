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
from awattar import AwattarClient

from string import Template
from datetime import timezone
from dateutil import tz
from datetime import timedelta

from influxdb import InfluxDBClient

data = None
config = None
client = None

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
				
		json_body = [{
				"measurement": "Energy marketprice",
				"time": item.start_datetime.astimezone(tz.UTC).isoformat(),
				"fields": {
					"value": item.marketprice
				}
			}]

		result = client.write_points(json_body,protocol=u'json',time_precision='s')

def parseConfig():
	"""
    Read config file and parse all Task sections

    """	
	global config
	global data
	global client

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

				starttime_slot = datetime.datetime.now()
				starttime_slot = starttime_slot.replace(hour=config.getint(section, 'Starttime'))	
				endtime_slot = starttime_slot + timedelta(hours=config.getint(section, 'Periode'))

				#get best start time 
				best_slot = client.best_slot(config.getfloat(section, 'Duration'),starttime_slot, endtime_slot)
				print(f'Best slot {best_slot.start_datetime:%Y-%m-%d %H:%M:%S} - {best_slot.end_datetime:%Y-%m-%d %H:%M:%S} - {(best_slot.marketprice / 1000):.4f} EUR/kWh')
				
				endtime = best_slot.start_datetime + timedelta(minutes=60*config.getfloat(section, 'Duration'))

				#write start and end time to output
				templatefile = open(config.get(section, 'Template'))
				src = Template(templatefile.read())
				d={ 'Starttime':best_slot.start_datetime.strftime(config.get(section, 'Starttimepattern')), 'Endtime':endtime.strftime(config.get(section, 'Endtimepattern')) }
				outputfile = open(config.get(section, 'Output'),'w')
				outputfile.write(src.substitute(d))
				outputfile.close()	
				
		
def main(argv):
	"""
    Main routine

    """	
	global config
	global data
	global client
	
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
			print('awattar_scheduler.py --starttime=<hour> --periode=<hour> --duration=<hour>')
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


	client = AwattarClient('AT')

	#set start timestamp
	starttime_data = datetime.datetime.now(tz=timezone.utc)
	starttime_data = starttime_data.replace(hour=0, minute=0, second=0)		
	#set end timestamp
	endtime = starttime_data + datetime.timedelta(days=2)

	data = client.request(starttime_data, endtime)

	#return if response is empty
	if data == 0 or len(data) == 0:
		print('Can''t download data from server') 
		return

	#for item in data:
	#		print(f'{item.start_datetime:%Y-%m-%d %H:%M:%S} - {item.end_datetime:%Y-%m-%d %H:%M:%S} - {(item.marketprice / 1000):.4f} EUR/kWh')

	if len(opts) == 3:
		starttime_slot = datetime.datetime.now()
		starttime_slot = starttime_slot.replace(hour=starttime)	
		endtime_slot = starttime_slot + timedelta(hours=periode)

		#get best start time 
		best_slot = client.best_slot(duration,starttime_slot, endtime_slot)
		print(f'Best slot {best_slot.start_datetime:%Y-%m-%d %H:%M:%S} - {best_slot.end_datetime:%Y-%m-%d %H:%M:%S} - {(best_slot.marketprice / 1000):.4f} EUR/kWh')
		
	else:
		parseConfig()


if __name__ == "__main__":
	main(sys.argv[1:])
