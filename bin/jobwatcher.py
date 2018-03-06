import os
import sys
import argparse
import logging
import time
import re
import traceback
import subprocess


#@Author: John Gooch
#@Created: 20130715
#@Updated: 
#@Version: 1.0
#@Name: Job Status Watcher Script
#@Description: Watches job to enter the specified status before the specified timeout is reached or exceeded.


def initCLI():
	parser = argparse.ArgumentParser(description='Job Watcher utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument('-i', action="store", dest="interval", required=False,default="3s", help='Number of seconds to sleep. Ex 1s 1m 1h' )
	parser.add_argument('-t', action="store", dest="timeout", required=True,help='Timeout. Ex 1s 1m 1h' )
	parser.add_argument('-j', action="store", dest="job_name", required=True, help='Job status to watch.' )
	parser.add_argument('-p', action="store", dest="pattern", required=True, help='Regex pattern to watch for.' )
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

def getJobStatus( job_name ):
	cmd = None
	status = None
	if job_name:
		cmd = subprocess.Popen( "autostatus -J %s" %  ( job_name ), stdout=subprocess.PIPE)
		cmd_out, cmd_err = cmd.communicate()
	else:
		raise Exception( "Exception: Job name not supplied. job_name value=%s" % ( job_name ) ) 
	logger.debug( "Executing command %s." %  ( cmd ) )
	try:
		status = cmd_out.strip()
		logger.debug( "Job status s %s" % ( status ) )
		return status
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
		return jobwatcher( args.job_name, args.pattern, sleep_seconds, timeout_seconds, args.negative_logic )
	except Exception, err:
		logger.error( "Exception while watching job %s. Reason: %s" % ( args.job_name,str(err) ) )
		traceback.print_exc()
		return 2


if __name__ == "__main__":
	sys.exit(main())