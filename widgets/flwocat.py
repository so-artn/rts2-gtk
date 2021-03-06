#!/usr/bin/python
"""Loads catalogue from disk file."""

# (C) 2011 Petr Kubanek, Institute of Physics <kubanek@fzu.cz>

import sys
import subprocess
import targets
import re

class FLWOCat:
	def __init__(self):
		self.tarid = None
		self.pi = None
		self.program = None

	def run_cmd(self,cmd,read_callback=None):
		print cmd
		proc = subprocess.Popen(cmd,stdout=subprocess.PIPE)
		if read_callback:
			while (True):
				a=proc.stdout.readline()
				if a:
					read_callback(a)
				else:
					break

		return proc.wait()
	
	def parse_script(self,scr):
		ret = ''
		s = scr.split(',')
		for se in s:
		  	fil = se.split('-')
			ret += 'filter=' + fil[0] + ' ';
			if (int(fil[2]) > 1):
				ret += 'for ' + fil[2] + ' { E ' + fil[1] + ' }'
			else:
			  	ret += 'E ' + fil[1]
			ret += ' '
		return ret
	
	def process_newtarget(self,line):
		m = re.search ('#(\d+)',line)
		if m:
			self.tarid = m.group(1)
			print 'Target ID is %s' % (self.tarid)
	
	def parsePiProg(self,line):
		pi = re.match(r'^\!P.I.:\s*(\S.*)$', line)
		if pi:
			self.pi = pi.group(1)
			return
		program = re.match(r'^\!Program:\s*(\S.*)$', line)
		if program:
		  	self.program = program.group(1)
			return
		print >> sys.stderr, 'Unknow ! line: {0}'.format (line)
		exit (1)

	def loadCatalogue(self,filename):
		sched = open(filename)
		ret = []
		for l in sched.readlines():
		  	l=l.rstrip()
			if (len(l) == 0):
			  	continue
			if l[0] == '#' and len(l) > 1 and l[1] == '!':
			  	self.parsePiProg(l[1:])
				continue
			if l[0] == '!':
			  	self.parsePiProg(l)
				continue
			a = l.split()
			if a[0][0] == '#':
			  	continue
			if (a[2][0] != '-' and a[2][0] != '+'):
			  	a[2] = '+' + a[2]

			self.run_cmd(["rts2-newtarget", '-m', a[0], a[1] + ' ' + a[2]],self.process_newtarget)

			if self.tarid is None:
				print >> sys.stderr, 'rts2-newtarget does not produces target ID, exiting'
				exit(0)
			# parse script
			script = self.parse_script(a[6])
			
			prior = int(a[11]) * 100
			if prior <= 0:
			  	prior = 1

			tempdis = a[8]
			if tempdis != '-1':
			  	if tempdis == '0':
			  		script = 'tempdisable 1800 {0}'.format(script)
				else:
			  		script = 'tempdisable {0} {1}'.format(tempdis,script)

			ampcen = a[9]
			autoguide = 'OFF'
			if a[10] == '1':
			  	autoguide = 'ON'

			script = 'ampcen={0} autoguide={1} {2}'.format(ampcen,autoguide,script)

			if len(a) > 15 and a[15] != 0:
				script = 'FOC.FOC_TOFF+={0} {1}'.format(float(a[15]),script)
	
			cmd = ["rts2-target", "-b", "0", "-e", "-p", str(prior), "-c", "KCAM", "-s", script]

	
			if float(a[13]) > 0:
				cmd.append("--airmass")
				cmd.append(":" + a[13])

			if float(a[14]) > 0:
				if float(a[14]) > 90:
					cmd.append("--lunarAltitude")
					cmd.append(":0")
				else:
					cmd.append("--lunarDistance")
					cmd.append(a[14] + ":")

			if int(a[7]) > 1:
			  	cmd.append("--maxRepeats")
				cmd.append(a[7])

			if self.pi is not None:
				cmd.append('--pi')
				cmd.append(self.pi)

			if self.program is not None:
			  	cmd.append('--program')
				cmd.append(self.program)

			cmd.append(self.tarid)

			self.run_cmd(cmd)
			ret.append(self.tarid)
		return ret
	
	def run(self):
		for arg in sys.argv[1:]:
			self.loadCatalogue(arg)

if __name__ == '__main__':
	a = FLWOCat()
	a.run()
