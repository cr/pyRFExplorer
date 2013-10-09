# -*- coding: utf-8 -*-

# RX-Explorer RS232 Interface
# http://code.google.com/p/rfexplorer/wiki/RFExplorerRS232Interface

from time import sleep
import serial
from multiprocessing import Process, Value, Queue, Manager
from Queue import Empty
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as img


class RFE( object ):

	def __init__( self, dev ):
		self.dev = serial.Serial( dev )
		self.dev.baudrate = 500000
		self.dev.timeout = 1.0
		self.mgr = Manager()
		self.config = self.mgr.dict()
		self.sweep_data = Queue()
		self.lcd_data = Queue()
		self.sweep_active = Value( 'b', False )
		self.serialer = Process( target=self.serial_worker, args=() )
		self.sweeper = Process( target=self.sweep_worker, args=() )
		self.lcder = Process( target=self.lcd_worker, args=() )
		self.start()
		self.Request_Config()

	def start( self ):
		self.sweeper.start()
		self.lcder.start()
		self.serialer.start()

	def stop( self ):
		self.serialer.terminate()
		self.lcder.terminate()
		self.sweeper.terminate()

	def write( self, data ):
	    """Sends data to RF-Explorer. Data can be a string or array.
	       Returns the number of bytes written.
	    """ 
	    return self.dev.write( data )

	def read( self, length=0, until=False ):
	    """Reads length bytes of data from the RF-Explorer and returns them
	       as string.
	    """
	    inp = ""
	    if until==False:
	      if length == 0:
	        inp += self.dev.read()
	      else:
	      	inp += self.dev.read( length )
	    else:
	      inp += self.dev.read( 2 )
	      while inp[-2:] != until:
	        inp += self.dev.read()
	    return inp

	def to_ascii( self, value, digits, binary=False ):
		if binary:
			b = bin(value)[2:]
			b = '0'*(digits-len(b))+b
			return b
		else:
			return ("%0"+digits+"d") % value

	def from_ascii( self, s, binary=False ):
		if binary:
			raise Exception('not implemented yet')
		else:
			return int(s)

	def send( self, command ):
		l = len( command )
		if l>62:
			raise Exception( 'command is longer than 62+2 bytes' )
		c = "#%c%s" % (chr(len(command)+2), command)
		self.write( c )

	def recv( self ):
		return self.read( until="\r\n" )

	def Current_Config( self, Start_Freq, End_Freq, Amp_Top, Amp_Bottom ):
		""" Send current Spectrum Analyzer configuration data.
		    It will change current configuration for RFE.
		"""
		c = "C2-F:%s,%s,%s,%s" % (Start_Freq, End_Freq, Amp_Top, Amp_Bottom)
		self.send( c )

	def Request_Config( self ):
		""" Request RFE to send Current_Config
		"""
		c = "C0"
		self.send( c )

	def Request_Hold( self ):
		""" Stop spectrum analyzer data dump
		"""
		c = "CH"
		return self.send( c )

	def Request_Shutdown( self ):
		""" Shutdown RF Explorer unit
		"""
		c = "CS"
		self.send( c )

	def Enable_DumpScreen( self ):
		""" Request RFE to dump all screen data. It will remain active until
		    Disable_DumpScreen is sent. 
		"""
		c = "D1"
		self.send( c )

	def Disable_DumpScreen( self ):
		""" Request RFE to stop dumping screen data
		"""
		c = "D0"
		self.send( c )

	def Change_Baudrate( baudrate ):
		""" Switch RF Explorer communication baudrate. The switch is immediate and it is
		    lost after a reset. Reliable and recommended communication baudrates are 2400bps
		    and 500Kbps only.
		    Codified baudrate values are: 0-500Kbps, 1-1200bps, 2-2400bps,
		    3-4800bps, 4-9600bps, 5-19200bps, 6-38400bps, 7-57600bps, 8-115200bps
		"""
		c = "Cc%s" % baudrate
		self.send( c )

	def Disable_LCD( self ):
		""" Request RFE to switch LCD OFF and stop all draw activity
		"""
		c = "L0"
		self.send( c )

	def Enable_LCD( self ):
		""" Request RFE to switch LCD back ON and resume all draw activity
		"""
		c = "L1"
		self.send( c )

##################################################################################################
# Serial Worker World

	def serial_worker( self ):
		while True:
			cmd = self.recv()
			cmd = cmd[:-2]  # chomp EOL
			if cmd[:2] == '$S':
				if self.sweep_active.value == True:
					self.decode_sweep( cmd[3:] )
			elif cmd[:2] == '$D':
				self.decode_lcd( cmd[3:] )
			elif cmd[:6] == '#C2-M:':
				self.decode_setup( cmd[7:] )
			elif cmd[:6] == '#C2-F:':
				self.decode_config( cmd[7:] )
			else:
				pass  # ignore faulty reads

	def decode_setup( self, setupstr ):
		setupfields = ('Main_Model','Expansion_Model','FirmwareVersion')
		setuparray = setupstr.split( ',' )
		sup = dict( zip( setupfields, setuparray ) )

		# Decode fields
		for f in ('Main_Model','Expansion_Model'):
			sup[f] = int( sup[f] )

		main_model = {0:'433M',1:'868M',2:'915M',3:'WSUSB1G',4:'2.4G',5:'WSUSB3G'}
		sup['Main_Model'] = main_model[sup['Main_Model']]

		expansion_model = {0:'433M',1:'868M',2:'915M',3:'WSUB1G',4:'2.4G',5:'WSUB3G', 255:''}
		sup['Expansion_Model'] = expansion_model[sup['Expansion_Model']]

		# update managed dict
		for k,v in sup.items():
			self.config[k] = v

	def decode_config( self, configstr ):
		configfields = ('Start_Freq','Freq_Step','Amp_Top','Amp_Bottom','Sweep_Steps',
			'ExpModuleActive','CurrentMode','Min_Freq','Max_Freq','Max_Span','RBW',
			'Db_Offset','UNDOCUMENTED')
		configarray = configstr.split( ',' )
		if len(configarray) != len(configfields):
			raise Exception( 'received unexpected number of config values' )
		cfg = dict( zip( configfields, configarray ) )

		# Decode fields
		for f in configfields:
			cfg[f] = int( cfg[f] )

		cfg['ExpModuleActive'] = cfg['ExpModuleActive'] == 1

		current_mode = {0:'SPECTRUM_ANALYZER',1:'RF_GENERATOR',2:'WIFI_ANALYZER',255:'UNKNOWN'}
		cfg['CurrentMode'] = current_mode[cfg['CurrentMode']]

		# update managed dict
		for k,v in cfg.items():
			self.config[k] = v

	def decode_lcd( self, lcdstr ):
		mem = []
		for b in lcdstr:
			b = ord(b)
			mem += [b >> i & 1 for i in xrange(7,-1,-1)]
		if len(mem) < 128*64:
			mem = [0]*(128*64-len(mem)) + mem #TODO: wtf! missing byte at beginning of memory
		lcd = np.zeros( dtype=np.int, shape=(64,128) )
		for y in xrange( 64 ):
			for x in xrange( 128 ):
				p = (y/8)*8*128 + x*8 + (7-y%8)
				lcd[y][x] = mem[p]
		self.lcd_data.put_nowait( lcd )

	def decode_sweep( self, sweepstr ):
		sweep_db = [-float(ord(x))/2.0 for x in sweepstr]
		sweep_start = 1000 * self.config['Start_Freq']
		sweep_step = self.config['Freq_Step']
		sweep_end = sweep_start + sweep_step * self.config['Sweep_Steps']
		sweep_freq = range( sweep_start, sweep_end, sweep_step )
		sweep = zip( sweep_freq, sweep_db )
		self.sweep_data.put_nowait( sweep )

##################################################################################################
# LCD Plot Worker World

	def lcd_worker( self ):
		while True:
			lcd = self.lcd_data.get()
			imgplot = plt.imshow( lcd )
			plt.draw()
			plt.show()

##################################################################################################
# Sweep Plot Worker World

	def sweep_worker( self ):
		while True:
			sweep = self.sweep_data.get()
			print sweep
