import ConfigParser
import argparse
import logging
import os
import pyodbc
import sys
import traceback

import asys


#@Version: 2.2
#@Author: John Gooch
#@Created: 20130501
#@Updated: 20131217
#@Name: MS SQL Server Query Command line utility
#@Description: Connects to MS SQL Server database and executes sql query
#@2.2 Added debug statements for improve troubleshooting.
#@2.1 fixed incorrect method of determining records returned. restructured flow to cleanly allow for both data read and data changing statements
#@2.0 20130813 Added output file path, row_count, and cleaned up logic quite a bit.
#@tasks

def initCLI():
	parser = argparse.ArgumentParser(description='Connection to oracle db')
	parser.add_argument('-a', action="store", dest="auth_file_path", required=False, default=None, help="Path to the authentication credentials file.")
	parser.add_argument('-Q', action="store", dest="sql",required=False, default=None,help="SQL to execute upon connection. This overrides the conf file contents.")
	parser.add_argument('-f', action="store", dest="sql_file",required=False, default=None,help="Read SQL from file. This overrides the -Q contents.")
	parser.add_argument('-D', action="store", dest="db_name", required=True, help="Database Schema name.")
	parser.add_argument('-U', action="store", dest="db_user", required=False, help="Database user.")
	parser.add_argument('-P', action="store", dest="db_pwd", required=False, help="Database password.")
	parser.add_argument('-S', action="store", dest="db_server", required=True, help="Database server name.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None, help="Global variable to store scalar results.")
	parser.add_argument('-l', action="store", dest="level",  required=False, default="INFO", help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")
	parser.add_argument('-o', action="store", dest="output_file_path", required=False, help="Results file path.")
	parser.add_argument('-e', action="store_true", dest="error", required=False, default=False, help="Script returns exit code 1 when no records are returned.")
	try:
		args = parser.parse_args()
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None
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

def loadAuth( auth_file_path ):
	if os.path.exists(auth_file_path) == False:
		logger.error( "Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) ) 
		raise Exception( "Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) )
	auth = ConfigParser.RawConfigParser()
	auth.read(auth_file_path)
	db_user = auth.get( 'main', 'db_user' )
	db_pwd = auth.get( 'main', 'db_pwd')
	return ( db_user, db_pwd )
		
def getSQL( sql_file_path ):
	sql_file_path = os.path.realpath( sql_file_path )
	if not os.path.exists( sql_file_path ):
		raise Exception( "SQL file %s is not accessible." %  ( sql_file_path ) )
	sql_file = 	open( sql_file_path, 'r' )
	sql = sql_file.read()
	sql_file.close()
	return sql
		
		
def connect( server, database, user, password ):
	connection = None
	#connection = pymssql( server, database, user, password )
	connection = pyodbc.connect("DRIVER={SQL Server};SERVER=%s;DATABASE=%s;UID=%s;PWD=%s" % ( server, database, user, password  ) )
	logger.info("Connection to database %s on %s successful." % ( database, server   ) )
	return connection

#Execute a query statement that returns a resultset	
def execute( conn, sql, global_variable ):
	logger.debug( "Executing query %s." % ( sql ))
	logger.debug( "Global Variable %s." % ( global_variable ))
	logger.debug( "Starting execute. Query %s." % ( sql ))
	rows = None
	curs = None
	fields = None
	resultset = None
	row_count = 0
	curs = conn.cursor()
	logger.debug("Executing query %s" % ( sql ) )
	curs.execute(sql)
	if sql.strip().upper().startswith("SELECT"):
		logger.debug("SELECT statement detected. Retrieving recordset." )
		records = curs.fetchall()
		logger.debug("%d records retrieved." % ( len(records) ) )
		if len(records) == 0:
			logger.debug("No records returned from query." )
			if global_variable:
				logger.debug("Setting global variable %s to Null." % ( global_variable ) )
				asys.setGV(global_variable, None)
			curs.close()
			logger.debug( "No records returned. Row count = %d" % ( row_count ) )
			return None
		elif len(records) > 0:
			row_count = len(records)
			logger.debug( "%d records returned from query." % ( row_count ) ) 
			if global_variable:
				logger.debug( "Settting global vaiiable %s = %s" % ( global_variable, str(records[0][0]) )  )
				asys.setGV(global_variable, records[0][0])
				logger.info( "Global variable %s set to %s" % ( global_variable, records[0][0] ) )
			else:
				logger.info( "Global variable not specified so no global variable has been set." )
			logger.debug("Collecting field names.")
			columns = [column[0] for column in curs.description]
			curs.close() 
			logger.debug("There are %d fields. Field names are %s."  % ( len(columns), '.'.join(columns) )  )
			resultset = []
			resultset.append( columns )
			logger.debug( "Appending %d records to the resultset." % ( row_count ) )
			for record in records:
				resultset.append(record)
	else:
		logger.debug( "DML operation requested. Not returning any records." )
	return resultset

#print output to screen and optionally to the specified output file.
def printResults( records ):
	#Print the data to the screen
	for record in records:
		line = ','.join(map(str, record))
		print "%s\n" % ( line )
	return 0

def writeResults( records, output_file_path ):
	output_file = None
	output_file_path = os.path.realpath( output_file_path )
	output_dir_path = os.path.dirname( output_file_path )
	output_file_name = os.path.basename(output_file_path )
	
	if not os.path.exists( output_dir_path ):
		raise Exception( "Exception. Results file directory %s does not exist." % ( output_dir_path ) )
	output_file = open( output_file_path , 'w' )
	logger.debug( "Opened file %s for writing." % ( output_file_path) )
	for record in records:
		line = ','.join(map(str, record))
		output_file.write( "%s\n" % (line) )
	output_file.flush()
	output_file.close()
	logger.info( "Wrote resultset to results file %s." % ( output_file_path) )
	return 0

#Disconnects from the database
def disconnect( connection ):
	connection.close()
	return 0
		
def main():
	args = None
	logger = None
	conn = None
	resultset = None
	try:
		args = initCLI()
	except Exception, err:
		print traceback.print_exc()
		return 2

	try:
		logger = initLogging(args)
	except Exception, err:
		print print_exc()
		return 2 
		
	if args.auth_file_path:
		try:	
			( args.db_user, args.db_pwd ) = loadAuth(args.auth_file_path)
			logger.debug( "Credentials loaded from Auth file %s ."  % ( args.auth_file_path ) )
		except Exception, err:
			logger.error( "Exception loading credentials from authentication file. Reason: %s" ( str(err)) )
			print traceback.format_exc()
			return 2
			
	if not args.sql and not args.sql_file:
		logger.error( "Either -Q or -f must be specified. Exiting..." )
		return 2
	#read contents of sql file into sql paramter - overriding -Q argument
	#if -f not specified, contents of -Q will be used
	elif args.sql_file:
		args.sql = getSQL( args.sql_file ) 
	
	#connect to SQL Server db
	try:
		logger.debug( "Connecting to MS SQL Server DB %s on Server %s as User %s." % ( args.db_server, args.db_name, args.db_user ) )
		conn = connect( args.db_server, args.db_name, args.db_user, args.db_pwd )	
		logger.debug( 'Connected to %s db on %s server' % ( args.db_name, args.db_server  ) ) 
	except Exception, err:
		logger.error( "Exception connecting to %s db on server %s. Reason: %s" % ( args.db_name, args.db_server, str(err)  ) )
		print traceback.print_exc()
		return 2
			
	try:
		logger.debug( "Executing SQL statement %s" % ( args.sql ) )
		resultset = execute( conn, args.sql, args.global_variable )
		logger.debug( "Successfully executed SQL statement %s" % ( args.sql ) )
	except Exception,err:
		logger.error( "Exception running sql statement. Reason: %s" % ( str(err) ) ) 
		print traceback.print_exc()
		return 2

	try:
		logger.debug( "Closing database connection..." )
		disconnect(conn)
		logger.info( "Successfully disconnected from database." )
	except Exception, err:
		logger.error( "Exception while closing database connection. Reason: %s" % ( str(err) ) )
		print traceback.print_exc()
		return 2

	if not resultset:
		logger.info("No results returned. Exiting..." )
		if args.error:
			return 1
		else:
			return 0
	else:
		logger.info( "Query returned %d results." % ( len(resultset) -1 ) )
		try:
			logger.debug( "Printing resultset..." )
			printResults(resultset)
			logger.info( "Successfully printed resultset." )
		except Exception,err:
			logger.error( "Exception printing resultset. Reason: %s" % ( str(err) ))
			print traceback.format_exc()
			return 2

		try:
			if args.output_file_path:
				logger.debug( "Writing results to results file." )
				writeResults(resultset, args.output_file_path)
				logger.info( "Successfully wrote results to results file." )
			else:
				logger.debug( "Results not written to results file." )
		except Exception,err:
			logger.error( "Exception printing resultset. Reason: %s" % ( str(err) ))
			print traceback.format_exc()
			return 2
		return 0

if __name__ == "__main__":
	sys.exit(main())





