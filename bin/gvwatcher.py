import os
import sys
import argparse
import logging
import time
import re
import traceback
import subprocess


#@Author: John Gooch
#@Created: 20130717
#@Updated: 
#@Version: 1.0
#@Name: Global Variable Watcher Script
#@Description: Watches for specified global variable value for the specified number of seconds


def initCLI():
	parser = argparse.ArgumentParser(description='Global Variable watcher utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument('-i', action="store", dest="interval", required=False, default="3s", help='Number of seconds to sleep.' )
	parser.add_argument('-t', action="store", dest="timeout", required=True,help='Number of seconds to sleep.' )
	parser.add_argument('-g', action="store", dest="global_variable", required=True, help='Global variable to watch.' )
	parser.add_argument('-p', action="store", dest="pattern", required=True, help='Value to watch for.' )
	parser.add_argument('-n', action="store_true", dest="negative_logic", required=False, default=False,help='Return 0 if status does not match pattern.' )
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

def getGV( gvar ):
	cmd = None
	value = None
	if gvar:
		#cmd = ["autostatus", "-G", "%s" % ( gvar )  ]
		#cmd = "autostatus -G %s" %  ( gvar )
		cmd = subprocess.Popen( "autostatus -G %s" %  ( gvar ), stdout=subprocess.PIPE)
		cmd_out, cmd_err = cmd.communicate()
	else:
		raise Exception( "Exception: Global variable name not supplied. Gvar value=%s" % ( gvar ) ) 
	logger.debug( "Executing command %s." %  ( cmd ) )
	try:
		value = cmd_out.strip()
		logger.debug( "Value is %s" % ( value ) )
		return value
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		raise
	
def getSeconds( seconds_string ):
	seconds = 0
	try:
		int( seconds_string)
		return int(seconds_string)
	except:
		pass
	matches = re.match('(\d+)([A-Za-z])', seconds_string )
	if matches:
		number = int(matches.group(1))
		units =  matches.group(2)
		logger.debug( "numbers is %d. units is %s" % ( number, units ) )
		if units.upper() in "S":
			seconds = number
		elif units.upper() in "M":
			seconds = number * 60
		elif units.upper() in "H":
			seconds = number * 60 * 60
		else:
			raise Exception( "Exception: Invalid units %s."  %( units ) )
		return seconds
	else:
		raise Exception( "Exception. Unrecognized time format." )

def jobwatcher( job_name, pattern, sleep_seconds, timeout, negative_logic ):
	start_time = time.time()
	elapsed_time = 0
	status = None
	while elapsed_time < timeout:
		status = getJobStatus( job_name )
		logger.debug( "Comparing Value %s to pattern %s." % ( status, pattern ) )
		if negative_logic == False:
			if re.match( pattern, status,re.I ):
				logger.info( "Status %s matches pattern %s." % ( status, pattern ) )
				return 0
			else:
				logger.info( "Job status %s does not match pattern %s." % ( status, pattern ) )
		else:
			if not re.match( pattern, status, re.I ):
				logger.info( "Status %s negative logic matches pattern %s." % ( status, pattern ) )
				return 0
			else:
				logger.info( "Job status %s does not negative logic match pattern %s." % ( status, pattern ) )
		sleep( sleep_seconds )
		elapsed_time = int(time.time() - start_time )
	logger.info( "Elapsed time of %ds exceeds timeout of %ds." % ( elapsed_time, timeout ) )
	return 1

		
def gvwatcher( global_variable, pattern, sleep_seconds, timeout, negative_logic ):
	start_time = time.time()
	elapsed_time = 0
	value = None
	while elapsed_time < timeout:
		value = getGV( global_variable )
		logger.debug( "Comparing Value %s to watch value %s." % ( value, pattern ) )
		#if using positive logic
		if negative_logic == False:
			if re.match( pattern, value,re.I ):
				logger.info( "Global variable %s value %s matches pattern %s." % ( global_variable, value, pattern ) )
				return 0
			else:
				logger.info( "Global variable %s value %s does not match pattern %s." % ( global_variable,value, pattern ) )
		#if using negative logic
		else:
			if not re.match( pattern, value, re.I ):
				logger.info( "Global variable %s value %s negative logic matches pattern %s." % ( global_variable,value, pattern ) )
				return 0
			else:
				logger.info( "Global variable %s value %s does not negative logic match pattern %s." % ( global_variable,value, pattern ) )
		#Sleep the main thread for sleep_seconds
		sleep( sleep_seconds )
		#update the elapsed time value
		elapsed_time = int(time.time() - start_time )
	logger.debug( "Elapsed time of %ds exceeds timeout of %ds." % ( elapsed_time, timeout ) )
	return 1

		

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
		sleep_seconds = getSeconds( args.interval )
	except Exception, err:
		logger.error( "Exception parsing the sleep time. Reason: %s." % (str(err)) )
		traceback.print_exc()
		return 2

	try:
		timeout_seconds = getSeconds( args.timeout)
	except Exception, err:
		logger.error( "Exception parsing the sleep time. Reason: %s." % (str(err)) )
		traceback.print_exc()
		return 2

	try:
		return gvwatcher( args.global_variable, args.pattern, sleep_seconds, timeout_seconds, args.negative_logic )
	except Exception, err:
		logger.error( "Exception while watching global variable. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2


if __name__ == "__main__":
	sys.exit(main())