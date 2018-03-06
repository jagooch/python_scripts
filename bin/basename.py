#Template for Python Scripts
import argparse
import os
import sys
import os
import sys
import argparse
import os
import glob
import re
import logging
import subprocess

#@Version: 1.0 
#@Author: John Gooch
#@Created: 20121107
#@Updated: 
#@Name: Basebane Utility
#@Description: Prints the basename of a file and stores it in the specified global variable 
#@ Tasks


def initCLI():
	parser = argparse.ArgumentParser(description='Basename Utility.')
	parser.add_argument('-l', action="store", dest="level",  required=False, default="INFO", help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")
	parser.add_argument('-s', action="store", dest="src_file_path", required=True, help="Path to the older containing files t")
	parser.add_argument('-m', action="store", dest="mask", required=False, help="Text pattern to remove from the end of the file.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, help="Global variable to store the basename in.")
	
	try:
		args = parser.parse_args()
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None
	return args


	
#overrides command configuration file parameters with command line parameters, if specified. 
def loadArgs( args ):
	return 0

	
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
	
#verifies the required values have been provided on the command line or in the configuration file
def checkRequiredValues():
	#if not db_alias:
	#	logger.error( "Required value db_alias not provided. Exiting..." )
	#	return False

	return True

def setGV(gvar, value ):
	cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = None
	try:
		returncode = subprocess.call( cmd ) 
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		return 1
		
	if returncode != 0:
		logger.error("Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		return 1
	else:
		logger.info("Successfully set global variable  %s = %s" %  ( gvar, value ) )
		return 0
		
	
def basename( src_file_path, extension, gvar ):
	filename = os.path.basename( src_file_path )
	if extension:
		if filename.endswith( extension ):
			logger.debug( "Filename %s is %d characters long. Matching extension %s is %d chars long." % ( filename, len(filename), extension, len(extension)    ) )
			filename = filename[:-len(extension)]
	if gvar:
		if setGV( gvar, filename ) !=0:
			return 1
	print filename
	return 0
	
	
def main():
	global logger
	args = initCLI()
	if not args:
		print "No arguments supplied Exiting..."
		return 1
	logger = initLogging(args)
	if not logger:
		print "Failed to initialize logging.Quitting..."
		return 1

	if loadArgs(args) != 0: 
		return 1
	logger.debug( "Args loaded from command line to global vars")

	logger.debug( "Checking required values.")
	if checkRequiredValues() == False:
		return 1
	logger.debug( "Required values check passed.")

	if basename( args.src_file_path, args.mask, args.global_variable ) != 0:
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())





