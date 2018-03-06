import os
import shutil 
import sys
import logging
import argparse
import traceback


global logger
logging.basicConfig()
logger = logging.getLogger('delete_emptyfolders')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)


def initCLI():
	parser = argparse.ArgumentParser(description='Delete empty Folders v1.0')
	parser.add_argument('-l', action="store", dest="level", required=False, default="INFO",help="Debug level. Default is INFO")
	parser.add_argument('-s', action="store", dest="src_dir_path", required=True, help="Path to parent folder.")
	args = parser.parse_args()
	return vars(args)

def initLogging(level):
	#logger = logging.getLogger()
	levels = { 
		"DEBUG":logging.DEBUG, 
		"INFO" :logging.INFO,
		"WARNING":logging.WARNING, 
		"ERROR":logging.ERROR, 
		"CRITICAL":logging.CRITICAL
	}
	logger.setLevel( levels[level] )
	return

def delete_emptyfolders( src_dir_path ):
	for file in os.listdir( src_dir_path ):
		file_path = os.path.join( src_dir_path, file ) 
		if os.path.isdir( file_path ):
			if not os.listdir(file_path):
				logger.info( "Removing %s" % ( file_path ) )
				os.rmdir( file_path )
				logger.info( "%s removed." % ( file_path ) )
			else:
				logger.info( "%s is not empty. Skipping..." % ( file_path ) )
		else:
			logger.info( "%s is not a folder. Skipping..." % ( file_path ) )
	return 0
	

def main():
	mc = {}
	mc.update( initCLI() )
	initLogging( mc["level"] )
	try:
		return delete_emptyfolders(mc["src_dir_path"])
	except Exception,err:
		logger.error( "Failed to remove empty folders in %s. Reason: %s" % ( mc["src_dir_path"], str(err) ) )
		traceback.print_exc()
		return 2
	return 0

if __name__ == "__main__":
	sys.exit(main())