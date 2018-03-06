#move_asys

import argparse
import logging
import sys
import traceback

import asys

global logger
logging.basicConfig()
logger = logging.getLogger('setglobalvariable')
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
#@Created: 20150203
#@Updated:
#@Name: Set Globl Variable Script
#@Description: set the specified global variable to the specified value followed by a delay to allow the global variable update to take effect in the autosys database.
#@ Tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Set Global Variable v1.0')
	parser.add_argument('-g', action="store", dest="glo_name", required=True,help="Target global variable name.")
	parser.add_argument('-v', action="store", dest="glo_value", required=True, help="Value to be assigned to the global variable. A value of DELETE will delete the global variable.")
#	parser.add_argument('-d', action="store", dest="delay", required=False, type=int, default=5,help="Delay after global variable command is sent in seconds. Default is 5")
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

def setGlobalVariable( glo_name, glo_value ):
	asys.setGV(glo_name, glo_value)
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

	try:
		setGlobalVariable( mc['glo_name'], mc['glo_value'] )
		logger.info( "Global variable update successful." )
	except Exception, err:
		logger.error( "Failed to send the global variable command. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	return 0


if __name__ == "__main__":
	sys.exit(main());
