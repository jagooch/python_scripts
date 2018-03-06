#move_asys
import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
import logging
import ConfigParser
import glob
import subprocess

#@Author: John Gooch
#@Created: 20120810
#@Updated: 20129814
#@Version: 1.0
#@Name: Output Parser
#@Description: Parses output text files, reads and stores one line into a global variable.

def initCLI():
	parser = argparse.ArgumentParser(description='Reads job output from a text file and optionally stores the value in a global variable.')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument('-s', action="store", dest="source_file_path", required=True, help='Path to the job output file to read.')
	parser.add_argument('-c', action="store", dest="config_file_path", required=True, help='Path to the configuration file.')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
	parser.add_argument( '-g', action="store", dest="global_variable", required=True, help="Specify the global variable to store the output value in.")


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

def loadConfig(config_file_path):
	logger.debug("Loading configuration from configuration file %s" % ( config_file_path ) )
	conf = {}
	if ( os.path.exists(config_file_path) == False ):
		logger.error( "Failed to open credentials file %s. Please check path and permissions." % ( config_file_path) )
		return 1
	config = ConfigParser.RawConfigParser()
	config.read(config_file_path)
	conf['offset'] =  config.get('main', 'offset' )
#	conf['server'] =  config.get('main', 'server' )

	#this is a one-off, but if the config file specifies a log file path, then add and use it.
	if "log_file_path" in conf.keys():
		log_file_dirname = os.path.dirname(conf['log_file_path'] )
		if not os.path.exists(log_file_dirname):
			logger.error( "Failed to initialize logger log file. Please check path and permissions." % ( log_file_dirname ))
			return None
		formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s" )
		ch =  logging.handlers.TimedRotatingFileHandler( conf['log_file_path'] , when='d', interval=1, backupCount=3, encoding=None, delay=False, utc=False)
		ch.setFormatter(formatter)
		logger.addHandler(ch)
	return conf

def parseOutputFile(args, conf ):
	if os.path.exists(args.source_file_path) == False:
		logger.error("Cannot ready the source file %s. Please check path and permissions to this file." % ( args.source_file_path ) )
		return 1
	else:
		success = False
		target_line = int(conf['offset'])
		outputFile = open( args.source_file_path , "r" )
		count = 1
		while ( count <= target_line ):
			line = outputFile.readline().strip()
			if not line:
				logger.error("Error. Data not found in file. ")
				return 1
			else:
				if count != target_line:
					logger.debug( "Not reading the offset/target line. Index: %d Value: %s" % ( count, line ) )
					count += 1
					continue
				else:
					logger.debug( "Reading the offset/target Index: %d Value: %s" % ( count, line ))
					print line
					if args.global_variable:
						logger.debug( "Storing line %s into global variable %s"  % ( line, args.global_variable))
						if setGV( args.global_variable, line ) != 0:
							return 1
			count += 1
		outputFile.close()
		return 0

def setGV(gvar, value ):
	cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = subprocess.call( cmd, shell=True )
	if returncode != 0:
		logger.error("Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		return 1
	else:
		logger.info("Successfully executed command %s with exit code %d" %  ( " ".join( cmd ), returncode ) )
		return 0
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
	conf = loadConfig(args.config_file_path)
	if parseOutputFile(args, conf ) != 0:
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main());
