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

#@Version: 2.0
#@Author: John Gooch
#@Created: 20120501
#@Updated: 20120831
#@Name: Oracle SQl
#@Description: Connects to database and executes sql statements

#@tasks
#needs auth file load functions

def initCLI():
	parser = argparse.ArgumentParser(description='Connection to oracle db')
	parser.add_argument('-c', action="store", dest="config_file_path", required=False, help="Path to the configuration file.")
	parser.add_argument('-q', action="store", dest="sql_string",required=False, help="SQL to execute upon connection. This overrides the conf file contents.")
	parser.add_argument('-l', action="store", dest="level",  required=False, default="INFO", help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")
	parser.add_argument('-a', action="store", dest="auth_file_path", required=False, help="Path to the authentication credentials file.")
	parser.add_argument('-d', action="store", dest="db_alias", help="Database alias.")
	parser.add_argument('-u', action="store", dest="db_user", help="Database user.")
	parser.add_argument('-p', action="store", dest="db_pwd", help="Database password.")
	parser.add_argument('-o', action="store", dest="output_file_path", help="Database password.")
	parser.add_argument('--dml', action="store_true", dest="dml", required=False,default=False, help="DML flag.")

	
	try:
		args = parser.parse_args()
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None
	return args

	
def loadConfig(path):
	global db_alias 
	global db_user
	global db_pwd
	global sql_string
	global output_file_path
	global dml
	global auth


	#conf = {}
	if ( os.path.exists(path) == False ):
		logger.error( "Unable to access the configuration file %s. Please check path and permissions." % ( path ) )
		return 1
	try:	
		config = ConfigParser.RawConfigParser()
		config.read(path)
	except Exception, err:
		logger.error( "Failed to read config file %s. Check formatting of file. Reason: %s" % ( path, str(err) ) )
		return 1
	try:
		db_user = config.get('main', 'db_user')
		logger.debug( "db_user=%s" %(db_user))
	except:
		pass

	try:
		db_pwd = config.get('main', 'db_pwd')
		logger.debug( "db_pwd=%s" %(db_pwd))
	except:
		pass
	
	try:
		db_alias = config.get('main', 'db_alias')
		logger.debug( "db_alias=%s" %(db_alias))
	except:
		pass
	
	try:
		sql_string = config.get('main', 'sql_string')
		logger.debug( "sql_string=%s" %(sql_string))
	except:
		pass
		
	try:
		output_file_path = config.get('main', 'output_file_path')
		logger.debug( "output_file_path=%s" %(output_file_path))
	except:
		pass
		
	try:
		dml = True if config.get('main', 'dml') == "true" else False 
		logger.debug( "dml=%s" %(dml))
	except:
		pass

	return 0

	
#overrides command configuration file parameters with command line parameters, if specified. 
def loadArgs( args ):
	global db_alias 
	global db_user
	global db_pwd
	global sql_string
	global output_file_path
	global dml
	global auth

	try:
		if args.db_alias:
			db_alias = args.db_alias
			logger.debug( "db_alias = %s" % ( db_alias ))
	except:
		pass

	try:
		if args.db_user:
			db_user = args.db_user
			logger.debug( "db_user = %s" % ( db_user ))
	except:
		pass

	try:
		if args.db_pwd:
			db_pwd = args.db_pwd
			logger.debug( "db_pwd = %s" % ( db_pwd ))
	except:
		pass

	try:
		if args.sql_string:
			sql_string = args.sql_string
			logger.debug( "sql_string = %s" % ( sql_string ))
	except:
		pass

	try:
		if args.output_file_path:
			output_file_path = args.output_file_path
			logger.debug( "output_file_path = %s" % ( output_file_path ))
	except:
		pass
		
	try:
		if args.dml:
			dml = args.dml
			logger.debug( "dml = %s" % ( dml ))
	except:
		pass

	try:
		auth = args.auth_file_path
		logger.debug( "auth = %s" % ( auth ))
	except:
		pass
		
		
		
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

	
#executes INSERT, UPDATE, DELETE statements
def execDML( db_alias, db_user, db_pwd, query ):
	logger.debug( "Starting execDML. db_alias: %s db_user: %s db_pass: present query: %s" % ( db_alias, db_user, query ))
	curs = None
	conn = None
	try:
		conn = cx_Oracle.connect( "%s/%s@%s" % ( db_user, db_pwd, db_alias) )
		logger.debug("Connection to database successful." )
		curs = conn.cursor()
		logger.debug("Executing DML statement %s" % ( query ) )
		curs.execute(str(query))
		logger.debug( "%s rows affected by DML statement." % ( curs.rowcount ) ) 
		logger.debug("DML statment completed. Committing changes." )
		conn.commit()
		logger.debug("DML changes committed." )
		curs.close() 
		logger.debug("Cursor closed." )
		conn.close()
		logger.debug("DB connection closed." )
	except Exception, err:
		logger.error( "Failed to execute DML query. Reason: %s" % ( str(err) ) )
		return 1
	return 0


#Execute a query statement that returns a resultset	
def execQuery( db_alias, db_user, db_pwd, query, output_file_path=None ):
	logger.debug( "Starting execQuery. db_alias: %s db_user: %s db_pass: present query %s output_file_path: %s" % ( db_alias, db_user, query, output_file_path ))
	rows = None
	curs = None
	conn = None
	outfile = None
	fields = None
	try:
		conn = cx_Oracle.connect( "%s/%s@%s" % ( db_user, db_pwd, db_alias) )
		logger.debug("Connection to database successful." )
		curs = conn.cursor()
		logger.debug("Executing query %s" % ( query ) )
		curs.execute(query)
		logger.debug("Fetching results of query." )
		rows = curs.fetchall()
		logger.debug("%d rows fetched." % ( len(rows)  ) )
		if len(rows) == 0:
			logger.info( "No matching records found." )
		field_names = []
		count = 0
		logger.debug("Collecting field names.")
		logger.debug("%d field names are in each record."  % ( len(curs.description) ) )
		for record in curs.description:
			logger.debug( "Field name to add is %s.unt is %d" % ( record[0], count ) )
			field_names.insert( count, record[0] )
			logger.debug( "Added Field named: %s to list" % ( field_names[count] ) )
			count += 1
		fields = ','.join( field_names )
		curs.close() 
		conn.close()
	except Exception, err:
		logger.error( "Failed to execute query. Reason: %s" % ( str(err) ) )
		return 1
#print output to screen
	print "%s\n" % (fields)
	for row in rows:
		record = ','.join(map(str, row))
		print record
	if output_file_path:
		output_file = open( output_file_path , 'w' )
		output_file.write( "%s\n" % (fields) )
		for row in rows:
			record = ','.join(map(str, row)) 
			output_file.write( "%s\n" % (record) )
		output_file.close()
	return 0

	
def loadAuth( auth_file_path ):
	global db_user
	global db_pwd
	if os.path.exists(auth_file_path) == False:
		logger.error( "Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) ) 
		return 1

	auth = ConfigParser.RawConfigParser()
	auth.read(auth_file_path)		
		
	try:
		db_user = auth.get( 'main', 'db_user' )
	except Exception, err:
		logger.error( "Failed to read db_user value from authentication file %s. Reason: %s" % ( auth_file_path, str(err) ))
		return 1

	try:
		db_pwd = auth.get( 'main', 'db_pwd')
	except Exception, err:
		logger.error( "Failed to read db_pwd value from authentication file %s. Reason: %s" % ( auth_file_path, str(err) ))
		return 1
	return 0
	
	
#verifies the required values have been provided on the command line or in the configuration file
def checkRequiredValues():
	if not db_alias:
		logger.error( "Required value db_alias not provided. Exiting..." )
		return False
	if not db_user:
		logger.error( "Required value  db_user not provided. Exiting..." )
		return False
	if not db_pwd:
		logger.error( "Required value  db_pwd not provided. Exiting..." )
		return False
	if not sql_string:
		logger.error( "Required value  sql_string not provided. Exiting..." )
		return False
	if dml == None:
		logger.error( "Required value  dml not provided. Exiting..." )
		return False
	return True


def main():
	global logger
	#global dml
	#dml = False
	args = initCLI()
	if not args:
		print "No arguments supplied Exiting..."
		return 1
	logger = initLogging(args)
	if not logger:
		print "Failed to initialize logging.Quitting..."
		return 1

	if args.config_file_path:
		logger.debug( "loading config file")
		if loadConfig(args.config_file_path) != 0: 
			return 1
		logger.debug( "Config loaded")

	logger.debug( "Loading Args config file")
	if loadArgs(args) != 0: 
		return 1
	logger.debug( "Args loaded config file")

	logger.debug( "Loading Auth file")
	if args.auth_file_path:
		if loadAuth(args.auth_file_path) != 0:
			return 1
		logger.debug( "Auth file loaded")

	logger.debug( "Checking required values.")
	if checkRequiredValues() == False:
		return 1
	logger.debug( "Required values check  passed.")


	logger.debug( "Executing sql statement.")
	if dml == True:
		logger.debug( "dml=true. Running executeDML" )
		if execDML( db_alias, db_user,db_pwd,sql_string ) != 0:
			return 1
	else:
		logger.debug( "dml=false. Running executeQuery" )
		if execQuery( db_alias, db_user, db_pwd, sql_string, output_file_path ) != 0:
			return 1
	return 0


if __name__ == "__main__":
	sys.exit(main());





