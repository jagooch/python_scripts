#Template for Python Scripts
import os
import sys
import argparse
import ConfigParser
import re
import logging
import asys
import traceback 

global logger
logging.basicConfig()
logger = logging.getLogger('template')
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
#@Created: 
#@Updated: 
#@Name: 
#@Description: 
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Python Script Template v1.0')
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

def main():
	mc  = {} #master configuration dictionary that holds all command line and configuration file parameters
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

	return 0


if __name__ == "__main__":
	sys.exit(main())

