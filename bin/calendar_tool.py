import os
import sys
import argparse
import logging

#special case modules
import time
import string
import traceback
import subprocess

#@Version: 1.0 
#@Author: John Gooch
#@Created: 20130718
#@Updated: 
#@Name: Calendar Script
#@Description: Outputs the requested calendar property based on current date .


def initCLI():
	parser = argparse.ArgumentParser(description='Calendar script v1.0')
	#parser.add_argument('-p', action="store", dest="property",  required=True, help="Calendar property requested.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None,help="Global Variable.")
	parser.add_argument('-id', action="store", dest="input_date", required=False, default=None,help="Input/seed date. Use with -if")
	parser.add_argument('-if', action="store", dest="input_format", required=False, default=None,help="Input date format. Use with -id")
	parser.add_argument('-f', action="store", dest="format_string", required=False, default=r'%s',help="Format string used to format the output property.")
	parser.add_argument('-u', action="store_true", dest="uppercase", required=False, default=False,help="Return property in uppercase.")
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
				logger.debug("Successfully set global variable  %s = %s" %  ( gvar, value ) )
			else:
				logger.debug("Successfully DELETED global variable %s." %  ( gvar ) )
			return 0

		
def getDatetime( seed_date, format_string ):
	return time.strftime( format_string,seed_date )

	
def convertToDate( input_date, input_format ):
	logger.debug ( "Converting input time %s and format %s into time object." % ( input_date, input_format ))
	time_tuple =time.strptime( input_date, input_format )
	time_object = time.mktime( time_tuple )
	logger.debug( "Converted into time object representing %s." % ( time.strftime( "%m/%d/%Y", time_tuple ) ) )
	return time_tuple

	
def main():
	global logger
	global conf
	global args
	value = None #formatted string representing the calendar property
	seed_date = None
	try:
		args = initCLI()
	except argparse.ArgumentError, err:
		print "Invalid command line syntax. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	except Exception, err:
		print "Failed to parse command line arguments. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2
	
	try:
		logger = initLogging(args)
	except Exception, err:
		print "Failed to initialize logging. Reason: %s" % ( str(err) ) 
		traceback.print_exc()
		return 2

		
	if not (args.input_date and args.input_format ):
		try:
			seed_date = time.localtime()
		except Exception, err:
			logger.error( "Exception setting seed_date to current datetime. Reason: %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	else:
		try:
			seed_date = convertToDate( args.input_date, args.input_format )
		except Exception, err:
			logger.error( "Exception setting seed_date to supplied date %s and format %s. Reason: %s" % ( args.input_date, args.input_format,str(err) ) )
			traceback.print_exc()
			return 2
	logger.debug( "Seed date is %s" % ( seed_date) )	
	try:
		value = getDatetime( seed_date, args.format_string  )
		if args.uppercase:
			logger.debug("Setting value %s to uppercase." % ( value ) )
			value = value.upper()
			logger.debug("Value %s is uppercase." % ( value ) )
		else:
			logger.debug("Not setting value %s to uppercase." % ( value ) )
		print value
 	except Exception, err:
		logger.error( "Exception getting property. Reason: %s" % ( str(err) ) ) 
		traceback.print_exc()
		return 2

	if args.global_variable:
		try:
			logger.debug( "Setting Global variable %s to %s."  % ( args.global_variable, value   ))
			setGV( args.global_variable, value )		
			logger.debug( "Global variable %s set to %s."  % ( args.global_variable, value   ))
		except Exception, err:
			logger.error( "Exception setting global variable. Reason: %s" % ( str(err) ) ) 
			traceback.print_exc()
			return 2
	else:
		logger.debug( "Global variable argument not set." )
	return 0

if __name__ == "__main__":
	sys.exit(main());

"""

    %a - abbreviated weekday name
    %A - full weekday name
    %b - abbreviated month name
    %B - full month name
    %c - preferred date and time representation
    %C - century number (the year divided by 100, range 00 to 99)
    %d - day of the month (01 to 31)
    %D - same as %m/%d/%y
    %e - day of the month (1 to 31)
    %g - like %G, but without the century
    %G - 4-digit year corresponding to the ISO week number (see %V).
    %h - same as %b
    %H - hour, using a 24-hour clock (00 to 23)
    %I - hour, using a 12-hour clock (01 to 12)
    %j - day of the year (001 to 366)
    %m - month (01 to 12)
    %M - minute
    %n - newline character
    %p - either am or pm according to the given time value
    %r - time in a.m. and p.m. notation
    %R - time in 24 hour notation
    %S - second
    %t - tab character
    %T - current time, equal to %H:%M:%S
    %u - weekday as a number (1 to 7), Monday=1. Warning: In Sun Solaris Sunday=1
    %U - week number of the current year, starting with the first Sunday as the first day of the first week
    %V - The ISO 8601 week number of the current year (01 to 53), where week 1 is the first week that has at least 4 days in the current year, and with Monday as the first day of the week
    %W - week number of the current year, starting with the first Monday as the first day of the first week
    %w - day of the week as a decimal, Sunday=0
    %x - preferred date representation without the time
    %X - preferred time representation without the date
    %y - year without a century (range 00 to 99)
    %Y - year including the century
    %Z or %z - time zone or name or abbreviation
    %% - a literal % character
"""



