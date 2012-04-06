#!/usr/bin/env python

g_info = r'''
#
# downsamplah.py:	The MP3 down-sampler.  Version 0.1
#
# Purpose:	Take a collection of MP3's and create a copy of it, with the 
#		.mp3s re-encoded at a lower bitrate.  This is useful for 
#		saving space on portable MP3 players.
#
# Configuration:
#		To configure downsamplah for your enviornment, edit the
#		declarations at the top of the downsamplah.py text file with
#		your favorite text editor.
#		
# Requirements:	
#		On linux you'll need to have mpg321 and lame packages installed.
#
# Usage:
#	downsamplah.py	<src-dir> <dest-dir>	<target-bitrate>
#	e.g. downsamplah.py /home/me/mp3s /home/me/mp3s-small 128
#
# 	If you choose 0 for <target-bitrate> "--preset standard" will be used.
# Credits:	Created quickly by Aaron Fabbri on 10/02/2004.
#
'''
from ID3 import *		# from local directory
import os.path
import sys 

#---------------------------------------------------------------------------
# BEGIN Configuration Section; make changes here.
#

# Delete intermediate wav files?
g_delete_wav_files = 1

# fill in these functions for your platform.  I'm using Redhat 9 linux.
def platform_mp3_to_wav(mp3file, wavfile) :
	os.system("mpg321 -w \"%s\" \"%s\"" % (wavfile, mp3file))

def platform_wav_to_mp3(wavfile, mp3file, bitrate) :
	if bitrate:
	    os.system("lame -h -b %d \"%s\" \"%s\"" % 
		(bitrate, wavfile, mp3file))
	else:
	    os.system("lame --preset standard \"%s\" \"%s\"" % 
		(wavfile, mp3file))

# END Confituration Section
#---------------------------------------------------------------------------


#
# Implementaion
#

g_test = 0 

def usage() :
	print g_info
	sys.exit(0)

# Callback for os.path.walk which accumulates files in 'lst'
def walk_accumulate(lst, dirname, names) :
	for n in names:
		fullname = os.path.join(dirname,n)
		if os.path.isfile(fullname) and is_mp3(fullname) : 
			lst[fullname] = 1

def copy_id3(tgt_id3, src_id3) :
	for field in ["TITLE", "ARTIST", "ALBUM", "YEAR", "GENRE", "COMMENT", 
			"TRACKNUMBER"] :
		if src_id3.has_key(field) :
			tgt_id3[field] = src_id3[field]

def is_mp3(t) :
	if (t[len(t)-4:] == ".mp3" or t[len(t)-4:] == ".MP3") :
		return 1
	else:
		return 0

def dprintf(str) :
	if 1:
		print " *** "+ str 

class DownSamplah :
	def __init__(s, _src_path, _tgt_path, _bit_rate):
		s.tgt_bitrate = _bit_rate 
		s.src_path = os.path.normpath(_src_path)
		s.tgt_path = os.path.normpath(_tgt_path) 
		# relative to src_path
		s.srcfiles = {} 
		# relative to tgt_path
		s.tgtfiles = {} 
		s.needed_targets = []

	def get_needed_targets(s) :

		s.needed_targets = []
		s.srcfiles = {} 
		s.tgtfiles = {} 

		# get list of source files, existing target files
		os.path.walk(s.src_path, walk_accumulate, s.srcfiles)
		os.path.walk(s.tgt_path, walk_accumulate, s.tgtfiles)

		# which target files are missing?
		tidx = 0
		for sfile in s.srcfiles.keys() :
			sfile = os.path.normpath(sfile)
			mysrc = sfile[len(s.src_path)+1:]
			mytgt = os.path.normpath(os.path.join(s.tgt_path, mysrc))
			#dprintf("my src %s" % mysrc)
			#dprintf("my tgt %s" % mytgt)
			if s.tgtfiles.has_key(mytgt) :
				#dprintf("already have %s" % mysrc)
				None
			else :
				#dprintf("dont have tgt %s (src %s)" % 
				    #(mytgt, mysrc))
				s.needed_targets.append(mysrc)
		#done

	# Given list of full paths to each needed target file, determine
	# corresponding source files and re-encode them in the lower bitrate,
	# saving as target.
	def create_targets(s) :
		for t in s.needed_targets :

			dprintf("src_path %s, tgt_path %s" % (s.src_path, s.tgt_path))
			src = os.path.join(s.src_path, t)
			tgt = os.path.join(s.tgt_path, t)
					
			dprintf("src %s, tgt %s" % (src, tgt))
			# get ID3 tags
			srcID3 = ID3(src)
			dprintf(" src ID3: " + str(srcID3))
			
			# make sure target path exists 
			(tgt_dirpath, None) = os.path.split(tgt)
			if not os.path.exists(tgt_dirpath) :
				dprintf("Creating target path %s " % tgt_dirpath)
				if not g_test:
					os.makedirs(tgt_dirpath)

			# create temporary wav file
			tgt_wav = src[0:len(src) - 4] + ".wav"
			dprintf("Creating target wav " + tgt_wav)
			if not os.path.exists(tgt_wav) :
				platform_mp3_to_wav(src, tgt_wav)

			# now create new bitrate target
			platform_wav_to_mp3(tgt_wav, tgt, s.tgt_bitrate)
	
			if g_delete_wav_files :
				os.remove(tgt_wav)

			# copy over ID3 tags	
			tgtID3 = ID3(tgt)
			copy_id3(tgtID3, srcID3)
			if not g_test:
				tgtID3.write()


#
# Main program
#
if __name__ == "__main__" :
	if (len(sys.argv) != 4 and len(sys.argv) != 5) :
		usage()
	print(" **************************************")
	print(" *** Downsamplah 1.0 - Aaron Fabbri ***")
	print(" **************************************")
	_srcdir = sys.argv[1]
	_dstdir = sys.argv[2]
	_bitrate = int(sys.argv[3])
	dprintf("Src %s, Target %s, Bitrate %d" % (_srcdir, _dstdir, _bitrate))
	ds = DownSamplah(_srcdir, _dstdir, _bitrate)
	ds.get_needed_targets()
	ds.create_targets()
	dprintf("done")

