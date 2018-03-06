import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
import logging
import fileinput
import shutil 

#@Author:  John Gooch
#@Created: 20120618
#@Updated:
#@Version: 1.0
#@Name: Replace Text
#@Description: Finds and replaces text in a file

def initCLI():
	parser = argparse.ArgumentParser(description='Replace Text Utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO" )
	parser.add_argument('-f', action="store", dest="file_path", required=True, help='Path to the target file.')
	parser.add_argument('-m', action="store", dest="match",required=True , help='Text pattern to find within the text file.')
	parser.add_argument('-r', action="store", dest="replace", required=True, help='text to match withing the text file.')


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
		
def replace( file_path, match, replace ):
	replacement_count = 0
	if os.path.exists( file_path ) == False:
		logger.error( "Cannot access file %s. Please check file path and permissions." % ( file_path )) 
		return 1
	file_name = os.path.basename(file_path)
	dir_path = os.path.dirname(file_path)
	infile = open( file_path )
	outfile = open( "%s.replace" % ( file_path ) ,"w")
	#match = "(<entry key=\"includeMask\">)(.+)(</entry>)"
	while 1:
		line = infile.readline().strip()
		if not line:
			break
		old_line = line
		matches = re.search( match, line )
		if matches:
			logger.debug( "Line matches are %s" % ( str(matches.groups() )) )
			match_text = matches.group(2)
			logger.debug( "Match text for regex %s is %s." % ( match, match_text ))		
			new_line = line.replace( match_text, replace)
			logger.debug("New line is %s" % ( new_line))
			line = new_line
			replacement_count += 1
		else:
			logger.debug( "Line %s does not match regex pattern %s. group s %s" % ( line, match, match ))
		outfile.write(line + "\n")
	infile.close()
	outfile.close()
	#backup the input file 
	try:
		shutil.copy2( file_path , "%s.bak" % ( file_path) )
		logger.debug( "Original file %s successfully backed up to %s" % ( file_path , "%s.bak" % ( file_path ) ) )
	except Exception, err:
		logger.error( "Failed to backup file %s to %s.bak. Reason: %s" % ( file_path, file_path, str(err) ) )
		return 1
	#copy the replacement file over the original file
	try:
		shutil.copy2( "%s.replace" % ( file_path ), file_path )
		logger.debug( "Replacement file %s successfully copied over to original file %s" % ( "%s.bak" % ( file_path ), file_path  ) )
	except Exception, err:
		logger.error( "Failed to copy replace file %s over the original file %s. Reason: %s" % ( "%s.replace" % ( file_path ), file_path, str(err) ) )
		return 1
	if replacement_count == 0:
		logger.error( "No replacements performed. Exiting..." )
		return 1
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
	if replace( args.file_path, args.match, args.replace) != 0:
		logger.error( "Failed to find %s in file %s and replace with text %s. Exiting..."  % ( args.match, args.file_path, args.replace ) )
		return 1
		
	return 0


if __name__ == "__main__":
	sys.exit(main());