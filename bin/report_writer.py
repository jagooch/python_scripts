import cx_Oracle
import argparse
import os
import ConfigParser
import sys
import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
import logging
import logging.handlers
import csv

#@Author:  John Gooch
#@Created: 20120727
#@Updated:
#@Version: 1.0 
#@Name: Report Writer	
#@Description: Takes csv formatted data and creates reports using a transformation file

def initCLI():
	parser = argparse.ArgumentParser(description='File Zip utility')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	parser.add_argument('-c', action="store", dest="config_file_path", required=True, help='Path to the script configuration file.' )

	#parser.add_argument('-s', action="store", dest="source_file_path", required=True, help='Path to the source data file.' )
	#parser.add_argument('-d', action="store", dest="destination_file_path", required=True, help='Path to the output html file.')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
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
	ch =  logging.handlers.TimedRotatingFileHandler( "report_writer.log" , when='d', interval=1, backupCount=3, encoding=None, delay=False, utc=False)
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	
	return logger
		


def loadConfig(path):
	conf = {}
	if ( os.path.exists(path) == False ):
		print "Failed to open credentials file %s. Please check path and permissions." % ( path )
		return 1
	config = ConfigParser.RawConfigParser()
	config.read(path)
	conf['source_file_path'] = config.get('main', 'source_file_path')
	conf['destination_file_path'] = config.get('main', 'destination_file_path')
	conf['transformation_file_path'] = config.get('main', 'transformation_file_path')
	return conf

	
def create_report( source_file_path, destination_file_path, transformation_file_path=None ):
	#verify input file access
	if os.path.exists( source_file_path ) == False:
		logger.error( "Cannot access source file %s. Please check path and permissions."  % ( source_file_path  )  )
		return 1
	#verify the destination file path access
	filename = os.path.basename( destination_file_path )
	destination_directory = os.path.dirname( destination_file_path )
	if os.path.exists( destination_directory ) == False:
		logger.error( "Cannot access destinations directory %s. Please check path and permissions."  % ( destination_directory  )  )
		return 1
	
	# Open the CSV file for reading  
	reader = csv.reader(open( source_file_path, 'r' ) )   

	# Create the HTML file for output  
	htmlfile = open( destination_file_path, 'w' )  
	rownum = 0 
	#start the table
	htmlfile.write('<table border=1>')  
	for row in reader: # Read a single row from the CSV file  
		if rownum == 0:  
			htmlfile.write('<tr>') # write <tr> tag  
			for column in row:  
				htmlfile.write('<th>' + column + '</th>') # write header columns  
			htmlfile.write('</tr>') # write </tr> tag  
		else: # write all other rows  
			colnum = 1 
			htmlfile.write('<tr>')  
			for column in row:  
				htmlfile.write('<td>' + column + '</td>')  
				colnum += 1 
			htmlfile.write('</tr>')  
		rownum += 1 
	htmlfile.write('</table>') 
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
	if create_report( conf['source_file_path'], conf['destination_file_path'], conf['transformation_file_path'] ) != 0:
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main());