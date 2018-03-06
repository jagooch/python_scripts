#move_asys
import os
import sys
import logging
import re
import argparse
import glob
import traceback
import shutil
import subprocess

#@Author: John Gooch
#@name: Rename File
#@description: Renames file in directory that match pattern using substitution
#@Created: 20120430
#@Updated: 20130522

#@Version: 2.2 201305? - Added remote rename function.
#@Version: 2.1 20130517 - removed -m switch. simplified pattern matching. improved feedback.
#@Version: 2.0 20130517 - Made code layout standards compliant. Changes renaming algorithm to more close match OS native rename utility.
#@Version: 1.0

def initCLI():
	parser = argparse.ArgumentParser(description='Rename file utility.')
	parser.add_argument('-s', action="store", dest="src_dir_path",required=False, default=".", help="Target directory path.")
	parser.add_argument('-p', action="store", dest="pattern", required=True, help="Text to replace.")
	parser.add_argument('-r', action="store", dest="replace_pattern", required=True, help="Replacement text.")
	parser.add_argument('-g', action="store", dest="global_variable", required=False, default=None, help="Global variable to store # of renamed files.")
	parser.add_argument( '-e', action="store_true", dest="error", required=False, default=False, help="Exit code=1 if no files are renamed.")
	parser.add_argument( '-l', action="store", dest="level", required=False, default="INFO", help="Logging level. Default is INFO")
	return parser.parse_args()


def initLogging( level ):
	logger = logging.getLogger()
	if not level:
		logger.setLevel(logging.INFO)
	elif ( level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( level == "WARNING" ):
		logger.setLevel( logging.WARNING )
	elif ( level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	ch = logging.StreamHandler()
	ch.setFormatter(formatter)
	logger.addHandler(ch)
	return logger



def printHelp():
	return 0;

def setGV(gvar, value ):
	cmd = None
	if value is None:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=DELETE" % ( gvar )  ]
	else:
		cmd = ["sendevent", "-E", "SET_GLOBAL", "-G", "%s=%s" % ( gvar,value )  ]
	logger.debug( "Executing command %s." %  ( " ".join( cmd ) ) )
	returncode = None
	try:
		returncode = subprocess.call( cmd )
	except Exception, err:
		logger.error( "Failed to execute command %s. Reason: %s." % ( " ".join( cmd ), str(err) ) )
		raise
	else:
		if returncode != 0:
			raise Exception( "Failed to execute command %s. Exit Code: %d."  % ( " ".join( cmd ), returncode ) )
		else:
			if value:
				logger.debug("Successfully set global variable  %s = %s" %  ( gvar, value ) )
			else:
				logger.debug("Successfully DELETED global variable %s." %  ( gvar ) )
			return 0

def getTargetFiles( src_dir_path, file_mask ):
	target_files = []
	src_dir_path = os.path.realpath( src_dir_path )
	if not os.path.exists( src_dir_path):
		raise Exception( "Source directory path %s is not accessible or does not exist." % (src_dir_path) )
	elif not os.path.isdir( src_dir_path ):
		raise Exception( "Source directory path %s is not a directory." % (src_dir_path))
	else:
		files = os.listdir(src_dir_path)
		for file in files:
			src_file_path = os.path.join( src_dir_path, file )
			if not os.path.isfile( src_file_path ):
				continue
			else:
				if re.match( file_mask, file, re.I ):
					target_files.append( src_file_path )
				else:
					continue
		return target_files

def renameFiles( src_dir_path, pattern, replace_pattern, global_variable, error):
	file_paths = getTargetFiles( src_dir_path, pattern )
	rename_count = 0
	for file_path in file_paths:
			old_file_name = os.path.basename( file_path )
			old_dir_path = os.path.dirname( file_path )
			#re.match(
			#replace_string =
			new_file_name = re.sub( pattern, replace_pattern, old_file_name,re.I )
			logger.debug( "Old file %s New File %s" % ( old_file_name, new_file_name ) )
			logger.debug( "Old file name: %s Match:%s Replace:%s New File Name: %s" % ( old_file_name, pattern,replace_pattern, new_file_name ) )
			new_file_path = os.path.join( old_dir_path, new_file_name )
			if not os.path.exists( new_file_path):
				logger.debug("Renaming  %s to %s" % ( old_file_name, new_file_name ) )
				os.rename( file_path, new_file_path )
				rename_count+=1
				logger.info( "Renamed %s to %s" % ( file_path, new_file_path ) )
			elif (error ):
				logger.error( "Cannot rename %s to %s , destination file already exists." % ( file_path , new_file_path  ) )
				raise Exception( "Cannot rename %s to %s , destination file already exists." % ( file_path , new_file_path  ) )
			else:
				logger.error( "Cannot rename %s to %s , destination file already exists." % ( file_path , new_file_path  ) )
	if rename_count == 0 and error:
		logger.error( "No files were renamed." )
		return 1
	elif global_variable:
		setGV( global_variable, rename_count )

	return 0

def main(argv=None):
	global args
	global files
	global logger
	args = None
	files = None
	logger = None

	try:
		args = initCLI()
	except Exception, err:
		print "Error parsing the command line parameters. Reason: %s" % ( str(err)  )
		print traceback.format_exc()
		return 2

	try:
		logger = initLogging(args.level)
	except Exception, err:
		print "Error parsing the command line parameters. Reason: %s" % ( str(err)  )
		print traceback.format_exc()
		return 2

	# try:
		# files = getTargetFiles(args.src_dir_path, args.file_mask )
		# if len(files) == 0 and args.error:
			# return 1
	# except Exception, err:
		# logger.error( "Failed to list files in directory %s named like %s." % ( args.src_dir_path, args.pattern ) )
		# print traceback.format_exc()
		# return 2

	try:
		return renameFiles( args.src_dir_path, args.pattern,args.replace_pattern, args.global_variable,args.error )
	except Exception, err:
		logger.error("Error renaming files. Reason: %s." % ( str(err) ) )
		print traceback.format_exc()
		return 2;
	return 0

if __name__ == "__main__":
	sys.exit(main())
