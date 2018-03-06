import os
import re

src_dir_path = "."
file_mask = ".*\.json$"
file_list = []
for directory,subdirectories,files in os.walk( src_dir_path, topdown=False ):
	print "Processing directory %s" % directory
	for file in files:
		file_path = os.path.join( os.path.realpath(directory),  file )
		if re.match( file_mask, file, re.I ):
			#add the full file path to the file list
			print "adding file %s to the list" % file_path 
			file_list.append( file_path )
		else:
			print "File %s skipped." % file_path
	print "%s processed.\n\n" % directory
