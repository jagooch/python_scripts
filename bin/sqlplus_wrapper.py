import os
import sys
import argparse
from subprocess import Popen, PIPE
import logging
import traceback

version = "1.0"
#@Version: 1.0 
#@Author: John Gooch
#@Created: 20141017
#@Updated: 
#@Name: SQLPLUS Wrapper
#@Description: Runs SQLPLUS in shell to catch connection and file access issues as well as script issues.

global logger
logging.basicConfig()
logger = logging.getLogger('SQLPLUS_WRAPPER')
logger.setLevel(logging.INFO)


def initCLI():
	parser = argparse.ArgumentParser(description='SQLPLUS Wrapper 1.0')
	#parser.add_argument('-p', action="store", dest="property",  required=True, help="Calendar property requested.")
	parser.add_argument('-u', action="store", dest="username", required=False, default=None,help="DB username.")
	#parser.add_argument('-P', action="store", dest="password", required=False, default=None,help="DB user password.")
	parser.add_argument('-a', action="store", dest="auth_file_path", required=True, default=None,help="path to password file.")
	parser.add_argument('-s', action="store", dest="src_file_path", required=True, default=None,help="Path to target SQL.")
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	args = parser.parse_args()
	return vars(args)

	
def initLogging( level ):
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING,
		"ERROR":logging.ERROR ,
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level.upper()] )
	return
	
	
def initLogging( level ):
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING,
		"ERROR":logging.ERROR ,
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level.upper()] )
	return


def main():
	output = None
	mc = {}
	mc.update( initCLI() )
	initLogging(mc["level"])
	passwd = open( mc["auth_file_path"] , 'rb').readlines()[0]
	logger.debug( "passwd=%s" % ( passwd ) )
	if not os.path.exists( mc["src_file_path"] ):
		logger.error( "Failed to run sql statement. Error: File %s does not exist." % ( mc["src_file_path"] ) )
		return 1
	cmd = [ "sqlplus", "%s/%s" % ( mc["username"] , passwd ), "@%s" % (  mc["src_file_path"]  )   ]
	logger.debug( "The command line is %s" % ( ' '.join( cmd ) )  ) 
	#return 0
	try:
		p = Popen( cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE) 
		output = p.communicate(input='quit\n')[0]
		ec = p.returncode
		if ec:
			logger.error( "Failed to run sql statement. Error: %s. Exit code: %d" % ( output, ec ) ) 
			return 1
		else:
			logger.info( "Output is" )
			logger.info( output )
			logger.info( "Exit code is %d." % ( ec   ) )
	except Exception, err:
		logger.error( "Failed to run sql statement. Error: %s" ) 
		traceback.print_exc()
		return 1
	
	try:
		if "ORA-" in output:
			logger.error( "Oracle Error: %s" % ( output ) )
			return 1
		elif "SQL-" in output:
			logger.error( "SQL Error: %s" % ( output ) )
			return 1
		elif "ERROR" in output:
			logger.error( "Other Error: %s" % ( output ) )
			return 1
		return 1
	except Exception, err:
		traceback.print_exc()
		return 2
		
		

if __name__ == "__main__":
	sys.exit(main())