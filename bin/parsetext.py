import os
import sys
import argparse
import re
import logging

#special case modules
import time
import string
import traceback
import subprocess

#@Version: 1.0 
#@Author: John Gooch
#@Created: 20130718
#@Updated: 20130719
#@Name: Calendar Script
#@Description: Outputs the requested calendar property based on current date .


def initCLI():
	parser = argparse.ArgumentParser(description='Calendar script v1.0')
	parser.add_argument('-p', action="store", dest="pattern",  required=True, help="Text matching pattern.")
	parser.add_argument('-t', action="store", dest="text",  required=True, help="Text to parse.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None,help="Global Variable.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	args = parser.parse_args()
	return args

	
def initLogging(args):
	global logger
	logger = logging.getLogger()
	if not args.level:
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

	
def setGV(gvar, value ):
	cmd = None
	if value:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	else:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=DELETE" % ( gvar )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = None
	try:
		returncode = subprocess.call( cmd ) 
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		raise
	else:
		if returncode != 0:
			raise Exception( "Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		else:
			if value:
				logger.info("Successfully set global variable  %s = %s" %  ( gvar, value ) )
			else:
				logger.info("Successfully DELETED global variable %s." %  ( gvar ) )
			return 0

def parseText( mask, text, global_variable ):
	matches = re.match( mask, text, re.I)
	if not matches:
		logger.debug( "No matches for pattern %s found in text %s" % ( mask, text ) ) 
		if global_variable:
			logger.debug( "Setting global variable %s to None" % ( global_variable ) )
			setGV( global_variable, None )
		return 1
	else:
		match = matches.groups()[0]
		logger.info( "Match %s found for pattern %s in text %s " % ( match, mask, text ) )
		print match
		if global_variable:
			setGV( global_variable, match )
		return 0
		

	
def main():
	global logger
	global conf
	global args

	try:
		args = initCLI()
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2
	
	try:
		logger = initLogging(args)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.format_exc()
		return 2

	try:
		return parseText( args.pattern, args.text, args.global_variable )
	except Exception, err:
		print "Exception parsing text. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	return 0


if __name__ == "__main__":
	sys.exit(main());





