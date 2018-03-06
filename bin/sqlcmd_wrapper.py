import os
import zipfile
import sys
import argparse
import os
import glob
import zlib
import re
import logging
import subprocess
import ConfigParser
import string

#@Author:  John Gooch
#@Created: 20120516
#@Updated: 20120726
#@Version: 1.0
#@Name: SQLCMD Wrapper script
#@Description: Provides credentials from a secure locationa and the path to the correct python installation for the sqlcmd.py script to work.

def initCLI():
	parser = argparse.ArgumentParser(description='SQLCMD Wrapper Script')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
	#parser.add_argument('-a', action="store", dest="auth_file_path", required=True, help='Path to the authentication/credentials file.' )
	parser.add_argument('-c', action="store", dest="config_file_path", required=True, help='Path to the configuration file.')
	parser.add_argument('-d', action="store_true", dest="debug", default=False, help='Turn on debugging messages')
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO" )

	try:
		args, nargs = parser.parse_known_args()

		return args, nargs
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		return None

def initConfig( args ):
	conf = {}
	config = ConfigParser.RawConfigParser()
	config.read(args.config_file_path)
	conf['db_user'] = config.get('credentials', 'db_user')
	conf['db_pwd'] = config.get('credentials', 'db_pwd')
	conf['db_server'] = config.get('credentials', 'db_server')
	conf['db_name']  = config.get('credentials', 'db_name')
	conf['sqlcmd_path'] = config.get( 'main', 'sqlcmd_path')
	conf['python_path'] = config.get( 'main', 'python_path')
	return conf

#runs the python sql command written by Kurf Fehlhauer
def runSqlCmd(args, nargs, conf ):
	#options = " ".join( nargs )

	cmd = [ conf['python_path'], conf['sqlcmd_path'], '-S',  conf['db_server'], '-d',  conf['db_name'], '-U', conf['db_user'], '-P', conf['db_pwd'] ]
	for option in nargs:
		#if re.search( ".+=.+" , option):
		#	tokens = "=".split( option )
		# 	#tokens[1] = "\"%s\"" % ( tokens[1] )
		#	cmd.append( "%s=\"%s\"" % ( token[0], token[1]) )
		#elif re.search(" ", option ):
		#	cmd.append("\"%s\"" % ( option ) )
		#else:
		cmd.append(option)
	#check the command line file paths
	if os.path.exists(conf['python_path'] ) == False:
		print "Cannot access the python commnand %s. Please check path and permissions." % ( conf['python_path'] )
		return 1
	elif os.path.exists(conf['sqlcmd_path'] ) == False:
		print "Cannot access the sqlcmd script %s command. Please check path and permissions." % ( conf['sqlcmd_path'] ) 
		return 1

	print "Executing command array contains %s" %( cmd )
	#if subprocess.check_call( cmd ) != 0:
#		print "Failed to run command %s\nExiting..." % ( cmd )
#		return 1
	subprocess.check_call( cmd, shell=False  )

	return 0


def main():
	args, nargs = initCLI()
	if ( args is None ):
		print "Exiting..."
		return 1
	conf = initConfig(args)
	if conf is None:
		print "Exiting..."
		return 1
	elif 'sqlcmd_path' not in conf:
		print "missing required 'sqlcmd_path' item in config file."
		print "Exiting.."
		return 1
	elif 'python_path' not in conf:
		print "missing required 'python_path' item in config file."
		print "Exiting.."
		return 1

	print "args contains %s" % ( args )
	print "conf contains %s" % ( conf )
	print "nargs contains %s" % ( nargs )
	if runSqlCmd( args, nargs, conf ) != 0:
		print "Failed to execute the sqlcmd.\nExiting."
		return 1
	return 0;


if __name__ == "__main__":
	sys.exit(main());
