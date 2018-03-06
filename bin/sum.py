#Template for Python Scripts
import argparse
import logging
import sys
import traceback

import asys

global logger
logging.basicConfig()
logger = logging.getLogger('sum')
logger.setLevel(logging.ERROR)

#special case modules
#import glob
#import cx_Oracle
#import time
#import string
#import sendmail
#import zlib
#import zipfile

#@Version: 1.0 
#@Author: John Gooch
#@Created: 20150818
#@Updated: 
#@Name: Sum script
#@Description: Adds comma separated list of numbers . Optionally stores sum in global variable.
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Python Script sum v1.0')
	parser.add_argument('-v', action="store", dest="values", required=True, help="Comma separted list of numbers.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, help="Comma separted list of numbers.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	args = parser.parse_args()
	return vars(args)

def initLogging(level):
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING,
		"ERROR":logging.ERROR, 
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level] )
	return

	
def sum_values( values ):	
	total = 0	
	values_list = values.split( " " )
	#check for valid values
	for value in ( values_list ):
		total += float(value)
	return int(total)
	
def main():
	mc  = {} #master configuration dictionary that holds all command line and configuration file parameters
	total = 0
	try:
		#append command line arguments to master configuration 
		mc.update( initCLI() )
	except argparse.ArgumentError, err:
		logger.error( "Invalid command line syntax. Reason: %s" % ( str(err) )  )
		traceback.print_exc()
		return 2
	except Exception, err:
		logger.error( "Failed to parse command line arguments. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	
	try:
		initLogging( mc['level'])
	except Exception, err:
		logger.error( "Failed to initialize logging. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	try:
		total = sum_values( mc["values"] )
		logger.info( "Total is %d" % total )
		if mc["global_variable"]:
			asys.setGV(mc["global_variable"], str(total))
	except Exception, err:
		logger.error( "Failed to sum values. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	return 0


if __name__ == "__main__":
	sys.exit(main());

