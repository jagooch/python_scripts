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


#@Author: John Gooch 
#@Created: 20120813
#@Updated:
#@Version: 1.0
#@Name: MS SQL Command line wrapper
#@Description: Executes the sql command line tool while hiding the credentials from the command line.

def initCLI():
	parser = argparse.ArgumentParser(description='File Zip utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')

	parser.add_argument('-c', action="store", dest="config_file_path", required=True, help='Path to the configuration file.' )
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
	try:

		( args, options ) = parser.parse_known_args()
		print "Returning args: %s and options %s" % ( args, options )
		return (args, options )
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

def initLogging(args):
	logger = logging.getLogger()
	if not args.level is False:
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
		
def loadConfig(args):
	logger.debug("Loading configuration from configuration file %s" % ( args.config_file_path ) )
	conf = {}
	if ( os.path.exists(args.config_file_path) == False ):
		logger.error( "Failed to open configuration file %s. Please check path and permissions." % ( args.config_file_path) )
		return 1
	config = ConfigParser.RawConfigParser()
	config.read(args.config_file_path)
	conf['sqlcmd_path'] = config.get('main', 'sqlcmd_path' )
	conf['log_file_path'] = config.get('main', 'log_file_path' )

	#this is a one-off, but if the config file specifies a log file path, then add and use it.
	if conf['log_file_path']:
		log_file_dirname = os.path.dirname(conf['log_file_path'] )  
		if not os.path.exists(log_file_dirname):
			logger.error( "Failed to initialize logger log file. Please check path and permissions." % ( log_file_dirname ))
			return None
		formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s" )
		ch =  logging.handlers.TimedRotatingFileHandler( conf['log_file_path'] , when='d', interval=1, backupCount=3, encoding=None, delay=False, utc=False)
		ch.setFormatter(formatter)
		logger.addHandler(ch)
	
def sqlcmd( args, options, conf ):
	cmd = "%s -S %s -d %s -U %s -P %s %s" % ( conf['sqlcmd_path'], conf['db_server'],conf['db_instance'],conf['db_user'],conf['db_password'], args.config_file_path, " ".join( options ) ) 
	logger.debug( "Executing command %s" % ( cmd ) )
	output = None
	try:
		output = subprocess.check_output( cmd, shell=True )
		#print output
	except subprocess.CalledProcessError, err:
		logger.error( "Failed to run command %s. Reason: %s" % ( cmd, str(err) ) )
		return None
	lines = output.splitlines()
	


	return 0
	
def main():
	global logger
	( args, options ) = initCLI()
	if ( args is None ):
		print "Exiting..."
		return 1
	logger = initLogging(args)
	if logger is None:
		print "Failed to initialize logging.Quitting..."
		return 1;
	conf = loadConfig(args)
	if sqlcmd(args, options, conf) != 0:
		return 1
		
	return 0


if __name__ == "__main__":
	sys.exit(main());