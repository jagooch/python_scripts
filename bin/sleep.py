import os
import sys
import argparse
import ConfigParser
import logging
import time
import re
import traceback

#@Author: John Gooch
#@Created: 20120815
#@Updated: 20130712
#@Version: 1.0
#@Name: Sleep Script
#@Description: Sleeps for the specified number of seconds
#@ 1.1 20130712 replaced return codes with exception handling. Adding time parameter parsing to look for minutes, seconds, and hours


def initCLI():
	parser = argparse.ArgumentParser(description='Sleep utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.1')
	parser.add_argument('-t', action="store", dest="sleep_time", required=True, help='Number of seconds to sleep.' )
	parser.add_argument('-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
	try:
		return parser.parse_args()
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		raise

def initLogging(args):
	logger = logging.getLogger()
	if args.level is False:
		logger.setLevel(logging.WARNING)
	elif ( args.level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( args.level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( args.level == "WARNING" ):
		logger.setLevel( logging.WARNING )
	elif ( args.level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( args.level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger

def getSleepSeconds( sleep_time ):
	sleep_seconds = None
	try:
		int( sleep_time)
		return int(sleep_time)
	except:
		pass
	matches = re.match('(\d+)([A-Za-z])', sleep_time )
	if matches:
		number = int(matches.group(1))
		units =  matches.group(2)
		logger.debug( "numbers is %d. units is %s" % ( number, units ) )
		if units.upper() in "S":
			sleep_seconds = number
		elif units.upper() in "M":
			sleep_seconds = number * 60
		elif units.upper() in "H":
			sleep_seconds = number * 60 * 60
		else:
			raise Exception( "Exception: Invalid units %s."  %( units ) )
		return sleep_seconds
	else:
		raise Exception( "Exception. Unrecognized time format." )


def sleep( sleep_time ):
	logger.info("Sleeping for %d seconds starting at %s" % ( int(sleep_time),time.strftime("%H:%M:%S")  ) )
	time.sleep(float(sleep_time))
	logger.info("Awake at %s." % ( time.strftime("%H:%M:%S" ) ) )
	return 0
	
def main():
	global logger
	args = None
	sleep_seconds = 0
	
	try:
		args = initCLI()
	except Exception, err:
		print "Exception parsing the command arguments. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2
	try:
		logger = initLogging(args)
	except Exception, err:
		print "Exception while initializing logger. Reason: %s" % ( str(err) )
		traceback.print_exc()
		return 2

	try:
		sleep_seconds = getSleepSeconds( args.sleep_time )
	except Exception, err:
		logger.error( "Exception parsing the sleep time. Reason: %s." % (str(err)) )
		traceback.print_exc()
		return 2
		
	try:
		return sleep( sleep_seconds)
	except Exception, err:
		logger.error( "Exception while trying to sleep. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2


if __name__ == "__main__":
	sys.exit(main())