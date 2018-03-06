import ConfigParser
import argparse
import logging
import os
import re
import sys
import time
import traceback

import paramiko

import asys

global logger
logger = logging.getLogger('filewatcher')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

#@Version: 4.4
#@Author: John Gooch
#@Created: 20120905 
#@Updated: 20150101
#@Name: SFTP Script
#@Description: SFTP transfer script for uploads,downloads,  
#@ Tasks
#@fix upload destination file path handling

#4.4 20150113 Refactored functions to flag errors with exceptions, integrated asys module, made log messages clearer, separated connect/disconnect from the main functions.
#4.3 20130507 Added check for empty (double quoted) parameters 
#4.2 () Added remote file watcher function
#4.1 (20130225) removed paramiko logging to file setting. Removed requirement for destination folder when doing remote deletions.
#4.0 (20130213) Add remote file deletion
#3.2(20130213) Changed unrecognized command log message from info to error, and added "return 2" line. Added error switch and fixed download path handling
#3.1(20130206) Replaced "return 1" with exceptions. Fixed formatting and logging level on several messages
#3.0(20121206) Add UPLOAD_DELETE and DOWNLOAD_DELETE functions
#2.0 upload function and bugfixes
#1.0 download function


def initCLI():
	parser = argparse.ArgumentParser(description='SFTP transfer script. 4.0')
	parser.add_argument('-c', action="store", dest="config_file_path", required=False, help="Path to the configuration file.")
	parser.add_argument('-a', action="store", dest="auth_file_path", required=False, help="Path to the authentication file containing username and password.")
	parser.add_argument('-t', action="store", dest="transaction_type", required=True, help="Transaction type. Valid values are DOWNLOAD, UPLOAD, DOWNLOAD_DELETE, UPLOAD_DELETE, REMOTE_DELETE,REMOTE_FILEWATCH")
	parser.add_argument('-S', action="store", dest="hostname", help="Hostname of the remote server.")
	parser.add_argument('-U', action="store", dest="username", help="Logon Username.")
	parser.add_argument('-P', action="store", dest="password", help="Logon Password.")
	parser.add_argument('-p', action="store", dest="port",default=22,type=int, help="Remote port.")
	parser.add_argument('-s', action="store", dest="src_dir_path", help="Path to input/source folder. ")
	parser.add_argument('-d', action="store", dest="dst_dir_path", help="Path to destination/target/filewatch target folder.")
	parser.add_argument('-m', action="store", dest="file_mask", help="Regex file name pattern for files to operate on.")
	parser.add_argument('-l', action="store", dest="level",  required=False, default="INFO", help="Sets the debugging level. Valid arguments are DEBUG,INFO,ERROR.")
	parser.add_argument('-r', action="store", dest="retry_threshold",  required=False, help="Number of retry attempts for the current operation.")
	parser.add_argument('-e', action="store_true", dest="error",  required=False, default=False, help="Switch to throw error if no files are processed.")
	parser.add_argument('-g', action="store", dest="global_variable",  required=False, default=False, help="Name of global variable for file name.")
	parser.add_argument('-T', action="store", dest="timeout",  required=False, default="60s", help="Timeout for current operation.e.")
	parser.add_argument('-i', action="store", dest="interval",  required=False, default="10s", help="Time interval for file stat checks.")
		
	try:
		args = parser.parse_args()
		items = vars(args)
		for item in items.keys():
			#print "%s=%s" % ( item,items[item] ) 
			if type(items[item]) is str:
				if not items[item].strip():
					raise Exception( "Empty parameter %s." % ( item ) )
		return vars(args)
	except Exception, error:
		print "Failed to parse the command line arguments. Reason: %s" % ( error )
		raise

#load configuration information from configuration file
def loadConfig( path ):
	# global auth_file_path
	# global transaction_type
	# global hostname
	# global username
	# global password
	# global src_dir_path
	# global dst_dir_path
	# global port
	# global retry_threshold
	# global file_mask
	
	if ( os.path.exists(path) == False ):
		logger.error( "Unable to access the configuration file %s. Please check path and permissions." % ( path ) )
		raise Exception( "Unable to access the configuration file %s. Please check path and permissions." % ( path ) )
		
	try:	
		config = ConfigParser.RawConfigParser()
		config.read(path)
	except Exception, err:
		logger.error( "Failed to read config file %s. Check formatting of file. Reason: %s" % ( path, str(err) ) )
		raise


	try:
		auth_file_path = config.get('main', 'auth_file_path')
		logger.debug( "auth_file_path=%s" %(auth_file_path))
	except:
		pass

	try:
		transaction_type = config.get('main', 'transaction_type')
		logger.debug( "transaction_type=%s" %(transaction_type))
	except:
		pass
		
	try:
		hostname = config.get('main', 'hostname')
		logger.debug( "hostname=%s" %(hostname))
	except:
		pass

	try:
		username = config.get('main', 'username')
		logger.debug( "username=%s" %(username))
	except:
		pass
		
	try:
		password = config.get('main', 'password')
		logger.debug( "password=%s" %(password))
	except:
		pass
		
	try:
		src_dir_path = config.get('main', 'src_dir_path')
		logger.debug( "src_dir_path=%s" %(src_dir_path))
	except:
		pass	
		
	try:
		dst_dir_path = config.get('main', 'dst_dir_path')
		logger.debug( "dst_dir_path=%s" %(dst_dir_path))
	except:
		pass		
		
	try:
		port = int(config.get('main', 'port'))
		logger.debug( "port=%d" %(port))
	except:
		pass

	try:
		retry_threshold = int(config.get('main', 'retry_threshold'))
		logger.debug( "retry_threshold=%d" %(retry_threshold))
	except:
		pass		

	try:
		file_mask = config.get('main', 'file_mask')
		logger.debug( "file_mask=%s" % ( file_mask ) )
	except:
		pass
	

	try:
		error = config.get('main', 'error')
		logger.debug( "file_mask=%s" % ( file_mask ) )
	except:
		pass
	return config.items('main')

	
def initLogging(level ):
	if not level:
		logger.setLevel(logging.WARNING)
	elif ( level == "DEBUG" ):
		logger.setLevel( logging.DEBUG )
	elif ( level == "INFO" ):
		logger.setLevel( logging.INFO )
	elif ( level == "WARNING" ):
		loger.setLevel( logging.WARNING )
	elif ( level == "ERROR" ):
		logger.setLevel( logging.ERROR )
	elif ( level == "CRITICAL" ):
		logger.setLevel( logging.CRITICAL )
	else:
		raise Exception("Logging level %s not recognized." % ( level ) ) 
	return 0

	
def loadAuth( auth_file_path ):
	auth = None 
	if not os.path.exists(auth_file_path):
		logger.error( "Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) ) 
		raise Exception("Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) )
	else:
		auth = ConfigParser.RawConfigParser()
		auth.read(auth_file_path)
		return dict(auth.items('main'))
	# except Exception, err:
		# logger.error( "Error reading authentication file %s. Please check the format. Reason: %s" % ( auth_file_path, str(err) ))
		# raise Exception( "Error reading authentication file %s. Please check the format. Reason: %s" % ( auth_file_path, str(err) ))
		# raise
		
		#username = auth.get( 'main', 'username' )
	# except Exception, err:
		# logger.error( "Failed to read username value from authentication file %s. Reason: %s" % ( auth_file_path, str(err) ))
		# raise Exception( "Failed to read username value from authentication file %s. Reason: %s" % ( auth_file_path, str(err) ))

	# try:
		# password = auth.get( 'main', 'password')
	# except Exception, err:
		# logger.error( "Failed to read password value from authentication file %s. Reason: %s" % ( auth_file_path, str(err) ))
		# raise Exception( "Failed to read password value from authentication file %s. Reason: %s" % ( auth_file_path, str(err) ))
	# return 0
	
	


def connect( hostname, port, username, password ):
	client = None
	transport = paramiko.Transport(( hostname, port))
	#paramiko.util.log_to_file('paramiko.log')
	logging.getLogger("paramiko").setLevel(logging.WARNING)
	ssh = paramiko.SSHClient() 
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 

	#transport
	try:
		transport.connect(username=username, password=password ) 
	except Exception, err:
		logger.error( "Failed to connect to the remote server. Reason: %s" % ( str(err) ) )
		raise

	try:
		client = paramiko.SFTPClient.from_transport(transport)
		logger.debug( "Successfully connected to %s" % ( hostname ) ) 
		return client
	except Exception, err:
		logger.error( "Failed to start SFTP session from connection to %s. Check that SFTP service is running and available. Reason: %s" % ( hostname, str(err) ))
		raise

	
def download( sftp, src_dir_path, file_mask, dst_dir_path, error=False, delete_flag=False  ):
	dst_dir_path = os.path.realpath(dst_dir_path)
	delete_count = 0
	download_count = 0
	file_list = None
	if os.path.exists( dst_dir_path ) == False:
		logger.error( "Cannot access destination folder %s. Please check path and permissions. " % ( dst_dir_path ))
		raise Exception("Cannot access destination folder %s. Please check path and permissions. " % ( dst_dir_path ) )
	elif os.path.isdir( dst_dir_path ) == False:
		logger.error( "%s is not a folder. Please check path. " % ( dst_dir_path ))
		raise Exception("%s is not a folder. Please check path. " % ( dst_dir_path ))
	else:	
		
	# try:	
		sftp.chdir(src_dir_path)
		#file_list = sftp.listdir(path="%s" % ( src_dir_path ) )
		file_list = sftp.listdir()
	# except Exception, err:
		# logger.error( "Failed to list files in folder %s. Please check path and permissions. Reason: %s" % ( src_dir_path, str(err) ))
		# raise

		match_text = re.compile( file_mask )

		for file in file_list:         
			# Here is an item name... but is it a file or directory?         
			#logger.info( "Downloading file %s." % ( file ) )
			if not re.match( file_mask, file, re.I ):
				continue
			else:
				logger.info( "File \"%s\" name matched file mask \"%s\". matches %s.Processing file..." % ( file, file_mask, (match_text.match( file_mask ) ) ) )
			src_file_path = '/'.join( [ src_dir_path, file ] )
			logger.debug( "Source file path for %s is %s" % ( file, src_file_path ) )
			#Get source file size
			src_file_attr = sftp.stat( src_file_path )
			src_file_size = src_file_attr.st_size
			dst_file_path = os.path.join( dst_dir_path, file )
			retry_count = 0
			try:
				logger.info( "Downloading file %s to %s."  % ( src_file_path, dst_file_path ) )
				#sftp.get( file, dst_file_path, callback=printTotals ) #sftp.get( remote file, local file )
				sftp.get( src_file_path, dst_file_path) #sftp.get( remote file, local file )
				dst_file_attr =  os.stat( dst_file_path )
				dst_file_size = dst_file_attr.st_size
				#verify that source and destination file sizes match
				if src_file_size != dst_file_size:
					logger.error( "Error. Files source size %d and destination file size %d do not match." % ( src_file_size, dst_file_size ) )
					raise Exception("Error. Files source size %d and destination file size %d do not match." % ( src_file_size, dst_file_size ) )
				else:
					logger.debug( "source size %d and destination file size %d match." % ( src_file_size, dst_file_size ) )
					logger.info( "Successfully downloaded file %s to %s."  % ( file, dst_file_path ) )
					if delete_flag == True:
						logger.debug( "delete_flag is True. Deleting remote file %s from server." % ( src_file_path ) )
						sftp.unlink( src_file_path )
						logger.info( "Remote file %s successfully deleted from server." % ( src_file_path ) )
						delete_count +=1
				download_count += 1
			except Exception, err:
				if retry_count > retry_threshold:
					logger.error( "Failed to download %s to %s. Reason: %s." % ( src_file_path, dst_file_path, str(err) ) )
					sftp.close() 
					raise
				else:
					logger.error( "Failed to download %s to %s. Reason: %s." % ( src_file_path, dst_file_path, str(err) ) )
					retry_count +=1
							
		# sftp.close() 
		logger.info( "%d files downloaded from remote server." % ( download_count ) )
		logger.info( "%d files deleted from remote server." % ( delete_count ) )
		if error and download_count==0:
			raise Exception("No files downloaded from server." )

def upload( sftp, src_dir_path, mask, dst_dir_path, error=False, delete_flag=False  ):
	upload_count = 0
	delete_count = 0
	src_dir_path = os.path.realpath( src_dir_path )
	if os.path.exists( src_dir_path ) == False:
		logger.error( "Cannot access file source folder %s. Please check path and permissions. " % ( src_dir_path ))
		raise Exception( "Cannot access file source folder %s. Please check path and permissions. " % ( src_dir_path )  )
	elif os.path.isdir( src_dir_path ) == False:
		logger.error( "%s is not a folder. Please check path. " % ( src_dir_path ))
		raise Exception( "%s is not a folder. Please check path. " % ( src_dir_path ))
	else:	
		file_list = None
		file_list = os.listdir(src_dir_path )
		logger.debug( "Changing directory to %s" % ( dst_dir_path ) )
		sftp.chdir( dst_dir_path)
		logger.debug( "Changed directory to %s" % ( dst_dir_path ) )
		#match_text = re.compile( mask )

		for file in file_list:         
			if not re.match( mask, file, re.I ):
				continue
			else:
				logger.info( "File \"%s\" name matched file mask \"%s\". Processing file..." % ( file, mask ) )
			src_file_path = os.path.join( src_dir_path, file )
			logger.debug( "Source file path is %s" % ( src_file_path ) )
			src_file_attr = os.stat( src_file_path )
			src_file_size = src_file_attr.st_size
			dst_file_path = '/'.join( [ dst_dir_path, file ] )
			retry_count = 0
			try:
				logger.info( "Uploading file %s to %s."  % ( src_file_path, dst_file_path ) )
				sftp.put( src_file_path,  dst_file_path ) 
				dst_file_attr = sftp.stat( dst_file_path )
				dst_file_size = dst_file_attr.st_size
				if src_file_size != dst_file_size:
					logger.error( "Upload failed. Source file size %d does not match destination file size %d."  % ( src_file_size, dst_file_size ) )
					raise Exception( "Upload failed. Source file size %d does not match destination file size %d."  % ( src_file_size, dst_file_size ) )
				else:
					logger.info( "Successfully uploaded file %s to %s."  % ( src_file_path, dst_file_path ) )
					upload_count += 1
					logger.debug( "Source file size %d matches destination file size %d."  % ( src_file_size, dst_file_size ) )
					if delete_flag == True:
						os.remove( src_file_path )
						logger.info( "Successfully delete source file %s."  % ( src_file_path ) )
						delete_count += 1
			except Exception, err:
				if retry_count <= retry_threshold:
					retry_count +=1
					pass
				else:
					sftp.close()
					raise
					# logger.error( "Failed to upload %s to %s. Reason: %s." % ( src_file_path, dst_file_path, str(err) ) )
					# sftp.close() 
					# raise Exception( "Failed to upload %s to %s. Reason: %s." % ( src_file_path, dst_file_path, str(err) ) )
			logger.info( "%d local files uploaded." % ( upload_count ) )
			logger.info( "%d local files deleted." % ( delete_count ) )
		if error:
			if upload_count==0:
				logger.error("No files uploaded." )
				return 1
			elif delete_flag and delete_count==0:
				logger.error( "No files deleted." )
				return 1

def remote_delete( sftp, remote_dir_path, mask, error=False ):
	delete_count = 0
	try:	
		sftp.chdir(remote_dir_path)
		logger.debug( "Changed directory to %s" % ( remote_dir_path ) )
		file_list = sftp.listdir()
		logger.debug( "%s files found in directory %s" % ( len(file_list ), remote_dir_path ) )
	except Exception, err:
		logger.error( "Failed to list files in folder %s. Please check path and permissions. Reason: %s" % ( remote_dir_path, str(err) ))
		raise

	#file_mask  = re.compile( mask )
	for file in file_list:         
		# Here is an item name... but is it a file or directory?         
		#logger.info( "Downloading file %s." % ( file ) )
		if not re.match( mask, file, re.I ):
			logger.debug( "File %s name does not match pattern %s " % ( file, mask ) )
			continue
		else:
			logger.info( "File \"%s\" name matched file mask \"%s\". matches %s. Deleting file..." % ( file, file_mask, ( re.match( mask, file, re.I  ) ) ) )
		remote_file_path = '/'.join( [ remote_dir_path, file ] )
		retry_count = 0

		try:
			logger.debug( "Attempting to delete file %s."  % ( remote_file_path ) )
			sftp.unlink( remote_file_path )
			if file in ( sftp.listdir() ):
				sftp.close()
				raise Exception( "Failed to delete remote file %s." % ( remote_file_path ) )
			delete_count += 1
		except Exception, err:
			if retry_count > retry_threshold:
				logger.error( "Failed to delete remote file %s. Reason: %s " % ( remote_file_path, str(err) ) )
				raise
			else:
				logger.error( "Failed to delete remote file download %s. Reason: %s. Retrying..." % ( remote_file_path, str(err) ) )
				retry_count +=1
				pass
	logger.info( "%d files deleted from remote server." % ( delete_count ) )
	if error and delete_count==0:
		logger.error( "No files deleted from remote server." )
		return 1
	else:
		return 0

#finds a remote file based on search criteria.
def findfile( sftp, remote_dir_path, mask):
	files = None
	try:	
		sftp.chdir(remote_dir_path)
		logger.debug( "Changed directory to %s" % ( remote_dir_path ) )
		files = sftp.listdir()
		logger.debug( "%s files found in directory %s" % ( len(files ), remote_dir_path ) )
	except Exception, err:
		logger.error( "Failed to list files in folder %s. Please check path and permissions. Reason: %s" % ( remote_dir_path, str(err) ))
		raise

	if not files:
		logger.info( "No files found in %s matching file name pattern %s"  %  ( remote_dir_path, mask )  )
		return None
	elif len(files)==0:
		logger.info( "No files found in %s matching file name pattern %s"  %  ( remote_dir_path, mask )  )
		return None
	
	last_file_path = None
	last_file_mtime = None
	
	for file in files:         
		#Here is a file name... but is it a file or directory?         
		if not re.match( mask, file, re.I ):
			logger.debug( "File name %s does not match file name pattern %s " % ( file, mask ) )
			continue
		else:
			logger.debug( "File \"%s\" name matched file mask \"%s\"" % ( file, mask ) )
			file_path = '/'.join( [ remote_dir_path, file ] )
			stat = sftp.stat( file_path )
			mtime = stat.st_mtime
			if last_file_path:
				if mtime < last_file_mtime:
					last_file_path = file_path
					last_file_mtime = mtime
			else:
				last_file_path = file_path
				last_file_mtime = mtime 
			
	return last_file_path

	
#finds oldest file that matches the file name pattern. returns 0 if at least one file matches and is stable. returns 1 otherwise. Found file is stored in global variable is gv name is provided.
def remote_filewatch( sftp, remote_dir_path, mask, timeout, interval, global_variable=None, error=False ):
	remote_file_path = None
	file_list = None
	start_time = time.time() #keep track of duration vs timeout
	remote_file_name = None
	#detect presence of the file
	while True:
		try:
			remote_file_path = findfile( sftp, remote_dir_path, mask )
		except Exception, err:
			sftp.close()
			#logger.error( "Failed to find file matching %s in %s directory." % ( mask, remote_dir_path )  )
			raise
		if remote_file_path:
			break
		else: 
			current_time = time.time()
			#case when timeout is exceeded before seeing the file
			if ( current_time - start_time ) >= timeout:
				logger.info( "Filewatcher timed out watching for stable file matching %s in remote folder %s" % ( mask, remote_dir_path ) )
				return 1
			else:	
				time.sleep( interval )
	# if not remote_file_path:
		# raise Exception( "No file found in remote path %s that matches file name pattern %s" % ( mask ) ) 
	# else:
	stable_count = 0
	current_time = time.time()
	last_file_size = sftp.stat( remote_file_path ).st_size
	current_file_size = last_file_size
	logger.info( "Monitoring File %s. Starting file size is %d bytes." % ( remote_file_path, last_file_size ) )
	duration = current_time - start_time
	while duration < timeout :
		logger.info( "Sleeping %s seconds..." % ( interval ) )
		time.sleep( interval ) # sleep for interval seconds
		current_file_size = sftp.stat( remote_file_path ).st_size
		if last_file_size == current_file_size:
			stable_count += 1
			logger.debug( "File size is unchanged at %d. Stability Count is %d." % ( current_file_size, stable_count ) ) 
			if stable_count > 2:
				return 0
		else:
			logger.debug( "New files size is %d. Previous file size was %d." % ( current_file_size, last_file_size  ) ) 
			last_file_size = current_file_size
			stable_count = 0
		current_time = time.time()
		duration = current_time - start_time
	if stable_count > 2:
		logger.info( "File %s is stable at %d bytes."  % ( remote_file_path, current_file_size ) )
		return 0
	else:
		logger.info( "File %s NOT is stable at %d bytes."  % ( remote_file_path, current_file_size ) ) 
		return 1
	
def delete_local( ):
	return 0
	
def printTotals(transferred, toBeTransferred):
	logger.debug( "Transferred: {0}\tRemaining: {1}".format(transferred, toBeTransferred)  )
	return 0

def main():
	retry_threshold = 0
	sc = None
	mc = {}
	try:
		mc.update( initCLI() )
		logger.debug( "Command line arguments successfully parsed." )
	except Exception, err:
		logger.error( "Failed to parse command line arguments. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
		
	try: 
		logger.debug( "Initializing logging." )
		initLogging(mc["level"])
		logger.debug( "Logger initialized." )
	except Exception, err:
		logger.error( "Error: Failed to initialize logging. Reason: %s" % ( str(err) )  )
		traceback.print_exc()
		return 2
		
	if mc["config_file_path"]:
		try:
			logger.debug( "Loading configuration file parameters into global variables")
			mc.update(loadConfig( mc["config_file_path"]) )
			logger.debug( "Configuration file %s successfully loaded." % ( mc["config_file_path"]  ) )
		except Exception,err:
			logger.error( "Failed to load configuration file %s. Reason: %s" % ( mc["config_file_path"],str(err) ) )
			traceback.print_exc()
			return 2
	else:
		logger.debug( "Configuration file path not supplied. Skipping configuration file load.")


	if mc["auth_file_path"]:
		try:
			logger.debug( "Loading Auth file %s" % mc["auth_file_path"] )
			mc.update(loadAuth(mc["auth_file_path"]))
			logger.debug( "Auth file %s loaded" % ( mc["auth_file_path"] ) )
		except Exception, err:
			logger.error( "Failed to load credentials from authentication file %s. Reason: %s" % ( mc["auth_file_path"], str(err) ) )
			traceback.print_exc()
			return 2
	else:
		logger.debug( "Authorization file path not supplied. Skipping authorization file load.")

	#connect to the remote system and return the sftp client sc
	try:
		logger.debug( "creating connection using %s %s %s %s" % ( mc["hostname"], mc["port"], mc["username"], mc["password"] ) )
		sc = connect( mc["hostname"], mc["port"], mc["username"], mc["password"] )
		logger.debug( "Successfully connected to server %s" % ( mc["hostname"] ) ) 
	except Exception, err:
		logger.error( "Failed to connect to remote system. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
		
	#select an action
	#downloads remote files to local system
	if mc["transaction_type"] == "DOWNLOAD":
		try:
			download( sc, mc["src_dir_path"], mc["file_mask"], mc["dst_dir_path"], mc["error"], False )
			sc.close()
		except Exception, err:
			logger.error( "Failed to download file(s). Reason %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	#downloads and deletes remote files
	elif mc["transaction_type"] in "DOWNLOAD_DELETE":
		try:
			ec = download( sc, mc["src_dir_path"], mc["file_mask"], mc["dst_dir_path"], mc["error"], True )
			sc.close()
			return ec
		except Exception, err:
			sc.close()
			logger.error( "Failed to download and delete file(s). Reason %s" % ( str(err) ) )
			traceback.print_exc()
			return 2		
	#uploads local files
	elif mc["transaction_type"] == "UPLOAD":
		try:
			upload( sc, mc["src_dir_path"], mc["file_mask"], mc["dst_dir_path"], mc["error"], False )
			sc.close()
		except Exception, err:
			logger.error( "Failed to upload file(s). Reason %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	#uploads and deletes local files
	elif mc["transaction_type"] == "UPLOAD_DELETE":
		try:
			upload( sc, mc["src_dir_path"], mc["file_mask"], mc["dst_dir_path"], mc["error"], True )
			sc.close()
		except Exception, err:
			logger.error( "Failed to upload and delete file(s). Reason %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	#delete file from remote system
	elif mc["transaction_type"] == "REMOTE_DELETE":
		try: 
			ec = remote_delete( sc, mc["src_dir_path"], mc["file_mask"], mc["error"] )
			sc.close()
		except Exception, err:
			logger.error( "Failed to delete remote file(s). Reason: %s" % ( str(err) ) )
			traceback.print_exc()
			return 2
	elif mc["transaction_type"] == "REMOTE_FILEWATCH":
		try:
			ec = remote_filewatch(sc, mc["src_dir_path"], mc["file_mask"], asys.getSeconds(mc["timeout"]), asys.getSeconds(mc["interval"]), mc["global_variable"], mc["error"])
			sc.close()
			return ec
		except Exception, err:
			sc.close()
			logger.error( "Failed to filewatch remote file(s). Reason: %s" % ( str(err) ) )
			traceback.print_exc() 
			return 2
	elif mc["transaction_type"] == "REMOTE_RENAME":
		logger.error( "%s action is not yet implemented." % ( mc["transaction_type"] ) )
		#ec = remote_rename()
		#sc.close()
		return 2
	else:
		logger.error( "%s action is not valid." % ( mc["transaction_type"] ) )
		return 2

	return 0

if __name__ == "__main__":
	sys.exit(main());





