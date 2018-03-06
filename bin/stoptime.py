import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
import logging
import glob
import datetime
import shutil 
import time


#@Author: John Gooch
#@Created: 20120824
#@Updated: 20120827
#@Version: 1.0
#@Name: Stop Time Script
#@Description: Returns exit code 1 if the current time is equal to or greater that the specified stop time. 

def initCLI():
	parser = argparse.ArgumentParser(description='Stop Time Utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')

	parser.add_argument('-t', action="store", dest="stop_time", required=True, help='Time that script should start exiting with exit code 1.')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO" )
	try:
		args = parser.parse_args()
		return args
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

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
		
		
def stopTime( stop_time_string ):
	logger.debug("Original stop time string is %s" % ( stop_time_string ) )
	now = datetime.datetime.now()
	stop_time_string = "%s %s" % ( now.strftime( "%Y-%m-%d" ), stop_time_string ) 
	logger.debug("Modified stop time string is %s" % ( stop_time_string ) )
	stop_time = datetime.datetime.strptime( stop_time_string, "%Y-%m-%d %H:%M" )
	#stop_time =  datetime.datetime.strptime( "%s %s" % ( now.strftime( %Y-%m-%D  ) ,  stop_time_string ) , "%Y-%m-%d %H:%M") 
	logger.debug( "converted stop time string to %s. Current time string is %s." % ( stop_time.strftime( "%Y-%m-%d %H:%M"  ), now.strftime( "%Y-%m-%d %H:%M"  ) )  )
	if now >= stop_time:
		logger.debug( "The current time %s is on or after %s." % ( now.strftime( "%Y-%m-%d %H:%M"  ), stop_time.strftime( "%Y-%m-%d %H:%M"  ) ) )
		return 1
	logger.debug( "The current time %s is before %s. " % ( now.strftime( "%Y-%m-%d %H:%M"  ), stop_time.strftime( "%Y-%m-%d %H:%M"  ) ) )
	return 0
		
		
def main():
	global logger
	args = initCLI()
	if ( args is None ):
		print "Exiting..."
		return 1
	logger = initLogging(args)
	if logger is None:
		print "Failed to initialize logging.Quitting..."
		return 1;
	return stopTime( args.stop_time  )


if __name__ == "__main__":
	sys.exit(main());