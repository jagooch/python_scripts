import argparse
import asys
import ConfigParser
import datetime
import logging
import os
import re
import sys
import traceback
logging.basicConfig(level=logging.INFO)

#Import add on modules
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from email.Header import Header
import mimetypes

global logger
logger = logging.getLogger('filewatcher')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG)

#@Author: John Gooch
#@Created: 20120726
#@Updated: 20140919
#global version
version = "5.5"
#@Name: sendMail Script
#@Description: Sends email to recipients using SMTP protocol
#@Version: 5.5 20140919 - Made the -A (auth) switch optional.
#@Version: 5.4 20140502 - Logging and moved common functions into asys module.
#@Version: 5.3 20140421 - Added --auth switch for path to authentication file.
#@Version: 5.2 20131227 - Fixed multiple recipient bug and added CC field functionality.
#@Version: 5.1 20131219 - Fix bugs associated with loading and processing configuration files
#@Version: 5.0 20131213- added mimetype detection and -file switch for reading body content from file.
#@ added -e encoding switch to let the user specify the body encoding type.options are plain or html
#@4.0 20130613 Remove the extra newline characted inserted by the -b parameter
#@4.0 20130514 Added authentication to script(uname, pwd)
#@3.5 Fixed cc parsing and adding to email recipientlist
#@3.4 added merging of command line and configuration file parameters command line overrides the configuration file.


def initCLI():
	parser = argparse.ArgumentParser(description='SendMail Script')
	parser.add_argument( '-v','--version', action='version', version='%(prog)s {version}'.format(version=version) )
	#Path to the configuration file, useful for static or scheduled emails
	parser.add_argument('-c', action="store", dest="config_file_path", required=False, help='Path to the configuration file.' )
	#command line arguments needed to send an email out. This is more flexible and lets you use environment variables for the parameters
	parser.add_argument('-g', action="store", dest="server", required=False, help='Hostname of the SMTP gateway server.' )
	parser.add_argument('-f', action="store", dest="sender", required=False, help='Sender\'s email address.')
	parser.add_argument('-s', action="store", dest="subject", required=False, help='subject line for email.')
	parser.add_argument('-r', action="store", dest="recipients", required=False, help='Comma-separate list of recipient emails.')
	parser.add_argument('-b', action="store", dest="body", required=False, help='message body.')
	parser.add_argument('--file', action="store", dest="body_file_path", required=False, help='Path to file containing text for email body.', default=None)
	parser.add_argument('-a', action="store", dest="attachment_file_paths", required=False, help='Comma separated list of file paths to attach to email.', default=[])
	parser.add_argument('-A', '--auth', action="store", dest="auth_file_path", required=False, help='Path to file to authentication file.', default=None)
	#set the debug level
	parser.add_argument( '-l', action="store", dest="level", default="INFO", required=False, help="Sets the logging level for the script. Default is INFO")
	parser.add_argument( '--cc', action="store", dest="cc", required=False, default=None,help="Command separated list of email address for the cc field.")
	parser.add_argument( '-e', action='store' , dest='encoding', required=False, default='plain', help="Message body encoding.Values can be plain or html." )
	parser.add_argument( '-u', action='store' , dest='username', required=False, default=None, help="SMTP User." )
	parser.add_argument( '-p', action='store' , dest='password', required=False, default=None, help="SMTP Password." )

	return vars(parser.parse_args())

def initLogging(level):
	if not level:
		logger.setLevel(logging.WARNING)
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
	else:
		raise Exception( "Exception setting logging level. Unrecognised level %s was specified" %( level ) )
	return

def loadConfig(config_file_path):
	if not os.path.exists(config_file_path):
		raise Exception("Cannot access config file %s. Please check path and permissions." % ( config_file_path ) )
	config = ConfigParser.RawConfigParser()
	config.read(config_file_path)
	return dict( config.items('main') )

def loadAuth( auth_file_path ):
	auth = None
	if os.path.exists(auth_file_path) == False:
		logger.error( "Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) )
		raise Exception("Cannot access the authentication file %s. Please check the path and permissions." % ( auth_file_path) )
	auth = ConfigParser.RawConfigParser()
	auth.read(auth_file_path)
	return dict( auth.items('main') )

def readBody( file_body_path ):
	return open( file_body_path, 'r' ).readlines()

#detects the mimetype for a file
def get_file_mimetype (filename):
	format, enc = mimetypes.guess_type(filename)
	#mb = MIMEBase(*format.split('/'))
	"""Return the mimetype string for this file"""
	# result = None
	# if MIME_MAGIC:
		# try:
			# result = MIME_MAGIC.file(filename)
		# except (IOError):
			# pass
	return format


#converts plain text to UTF-8
def to_unicode (s):
    """Convert the given byte string to unicode, using the standard encoding,
    unless it's already encoded that way"""
    if s:
        if isinstance(s, unicode):
            return s
        else:
            return unicode(s, 'utf-8')


"""Convert the given unicode string to a bytestring, using the standard encoding, unless it's already a bytestring"""
def to_bytestring (s):
	if s:
		if isinstance(s, str):
			return s
		else:
			return s.encode('utf-8')


def sendMail( smtp_server, smtp_user,smtp_pwd,sender, subject, recipients, cc, body, files, encoding,replyto=None):
	recipient_list = []
	cc_list = []
	if recipients:
		recipient_list = recipients.split(',')
	if cc:
		cc_list = cc.split(',')
	"""Send a message to the given recipient list, with the optionally attached files"""
	logger.debug("smtp_server=%s" % ( smtp_server ) )
	logger.debug("smtp_pwd=%s" % ( smtp_pwd ) )
	logger.debug("sender=%s" % ( sender)  )
	logger.debug("subject=%s" % ( subject ) )
	logger.debug("recipient_list=%s" % ( recipient_list ) )
	logger.debug("cc_list=%s" % ( cc_list ) )
	logger.debug("body=%s" % ( body ) )
	logger.debug("body encoding = %s" % ( encoding ) )
	logger.debug("files=%s" % ( files ) )
	logger.debug("replyto=%s" % ( replyto ) )


	msg = MIMEMultipart()
	msg['From'] = sender.encode('ascii')
	# set the To address for the message header. Make sure email addresses do not contain non-ASCII characters
	if recipient_list:
		msg['To'] = COMMASPACE.join(map(lambda x: x.encode('ascii'), recipient_list))
	# set the Cc address for the message header. Make sure email addresses do not contain non-ASCII characters
	if cc_list:
		msg['Cc'] = COMMASPACE.join(map(lambda x: x.encode('ascii'), cc_list))
	logger.debug( "Message To is '%s'. Msg CC is '%s'" % ( msg['To'], msg['Cc'] ) )

	if replyto:
		# make sure email addresses do not contain non-ASCII characters
		msg['Reply-To'] = replyto.encode('ascii')
	msg['Date'] = formatdate(localtime=True)

	#always pass Unicode strings to Header, otherwise it will use RFC 2047 encoding even on plain ASCII strings
	msg['Subject'] = Header(to_unicode(subject), 'iso-8859-1')

	#always use Unicode for the body body, both plain and html content types
	if "html" in encoding:
		msg.attach(MIMEText(to_bytestring(body), 'html', 'utf-8'))
	else:
		msg.attach(MIMEText(to_bytestring(body), 'plain', 'utf-8'))

	for file in files:
		if not os.path.exists( file ):
			raise Exception( "Attachment %s is not accessible. Check the file path and permissions." % ( file ) )
		file_read_flags = "rb"
		try:
			mimestring = get_file_mimetype(file)
			if mimestring.startswith('text'):
				file_read_flags = "r"
			mimestring_parts = mimestring.split('/')
			part = MIMEBase(mimestring_parts[0], mimestring_parts[1])
		except AttributeError, IndexError:
			logger.error( "Failed to determine MIME type from mimestring %s. Reason: %s" % ( mimestring, str(IndexError) ) )
			# cannot determine the mimetype so use the generic 'application/octet-stream'
			part = MIMEBase('application', 'octet-stream')
			file_read_flags = "r"
			pass
		part.set_payload( open(file, file_read_flags).read() )
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="%s"' % ( os.path.basename(file) ) )
		msg.attach(part)

	smtp = smtplib.SMTP(smtp_server)

	if logger.level == logging.DEBUG:
		smtp.set_debuglevel(1)
	if smtp_user:
		if not smtp_pwd:
			raise Exception( "Password not specified for user %s."  % ( smtp_user ) )
		logger.debug("Logging into server %s as %s" %( smtp_server, smtp_user ) )
		smtp.login( smtp_user, smtp_pwd )

	results = smtp.sendmail( sender, recipient_list + cc_list, msg.as_string())
	#smtp.quit()
	smtp.close()
	if len(results):
		logger.error( "One more recipients refused." )
		logger.error("Sendmail results for each recipient." )
		for key in results.keys():
			logger.error( "%s=%s" % ( key, results[key]  ) )
		logger.error("End of sendmail results." )
		raise Exception("One more recipients refused.")
	elif not results:
		logger.info( "Successfully sent email to all recipients." )
		return 0

def readBody( body_file_path  ):
	if not os.path.exists( body_file_path ):
		raise Exception( "Cannot access Body File %s. Check file path and permissions." % ( body_file_path ) )
	f = open( body_file_path, 'r' )
	return f.read()



def main():
	files = []
	mc = {} #master configuration dictionary
	try:
		#parse command line arguments
		args = initCLI()
	except Exception, err:
		traceback.print_exc()
		logging.error( "Failed to initialize command line arguments. Reason %s" % ( str(err) ) )
		return 2
	for k,v in args.items():
		logging.debug( "mc %s = %s" % ( k,v ) )
		mc[k] = v

	try:
		initLogging(mc['level'])
	except Exception, err:
		logging.error( "Failed to initialize logging to level %s. Reason: %s" % ( mc['level'], str(err) ) )
		traceback.print_exc()
		return 2

	try:
		if mc['config_file_path']:
			config = loadConfig(mc['config_file_path'])
			for k,v in config.items():
				mc[k] = v

	except Exception, err:
		logger.error("Failed to load configuration file %s. Reason: %s" % ( mc['config_file_path'], str(err) ) )
		traceback.print_exc()
		return 2

	try:
		if mc['auth_file_path']:
			logger.debug( "Loading Auth file")
			auth = loadAuth(mc['auth_file_path'])
			logger.debug( "Auth file loaded")
			for k,v in auth.items():
				mc[k] = v
		else:
			logger.debug( "Authorization file path not supplied. Skipping authorization file load.")
	except Exception, err:
		logger.error( "Failed to load credentials from authentication file %s. Reason: %s" % ( mc['auth_file_path'], str(err) ) )
		traceback.print_exc()
		return 2

	try:
		if mc['body_file_path']:
			mc['body'] = readBody( mc['body_file_path'] )
	except Exception, err:
		logger.error( "Failed to read from body file. Reason: %s" % ( str( err ) ) )
		traceback.print_exc()
		return 2

	if mc['attachment_file_paths']:
		files = mc['attachment_file_paths'].split(',')

	#check that required fields are present and have values
	#mandatory_keys = [ 'server', 'username','password','sender', 'subject', 'recipients', 'body', 'encoding' ]
	mandatory_keys = [ 'server', 'sender', 'subject', 'recipients', 'body', 'encoding' ]
	try:
		for key in mandatory_keys:
			if key not in mc.keys():
				raise Exception( "KeyException. Master Configuration is missing key '%s'" % ( key ) )
			elif mc[key] is None:
				raise Exception( "ValueException. key '%s' value is '%s'" % ( key, mc[key] ) )
			else:
				logger.debug( "Key '%s' is in Master Configuration with value of '%s'" % ( key, mc[key] ) )
	except Exception, err:
		logger.error( "Failed Mandatory Keycheck. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2

	try:
		return sendMail( mc['server'], mc['username'], mc['password'], mc['sender'], mc['subject'], mc['recipients'],mc['cc'], mc['body'], files,mc['encoding'], None)
	except Exception, err:
		logger.error( "Error sending email. Reason: %s" % ( str(err) ) )
		traceback.print_exc()
		return 2
	return 0

if __name__ == "__main__":
	sys.exit(main());
