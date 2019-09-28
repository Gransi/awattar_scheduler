# awattar_scheduler
Scheduler for best price of energy from aWATTar Hourly (https://www.awattar.com/tariffs/hourly) and creates files based on templates.

This script replace the 'Starttime' and 'Endtime' identifier in the given template file and copy the output to the output location.

# Install

1. Copy the etc folder to the local folder
2. Copy awattar_scheduler.py to the /usr/local/bin folder

# Task configuration
Enable:
	Enable or Disabled task [true|false]
Starttime:
	Start hour
Periode:
	How many hours from start 
Duration:
	How many hours of usage. Get the best average price of electricty	
Template
	Path to template file
Output
	Copy the parsed template to output location
Starttimepattern:
	Format time to this string: eg: Time cron "0 %%M %%H * * ?" -> Time cron "0 0 13 * * ?"
Endtimepattern:
	Format time to this string: eg: Time cron "0 %%M %%H * * ?" -> Time cron "0 0 13 * * ?"
