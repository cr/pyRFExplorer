# -*- coding: utf-8 -*-

# RX-Explorer RS232 Interface
# http://code.google.com/p/rfexplorer/wiki/RFExplorerRS232Interface

from time import sleep
import sys
import serial
import multiprocessing
import threading

import numpy as np

class RFE( object ):

	def __init__( self, dev ):
		self.dev = serial.Serial( dev )
		self.dev.baudrate = 500000
		self.dev.timeout = 1.0
		self.mgr = multiprocessing.Manager()
		self.config = self.mgr.dict()
		self.sweep_data = multiprocessing.Queue()
		self.lcd_data = multiprocessing.Queue()
		self.sweep_active = multiprocessing.Value( 'b', False )
		self.serialer = multiprocessing.Process( target=self.serial_worker, args=() )
		self.start()
		self.Request_Config()
		# Wait until config is populated
		while len(self.config)<11:
			sleep( 0.1 )

	def start( self ):
		self.serialer.start()

	def stop( self ):
		self.serialer.terminate()

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
	        inp += self.read()
	    return inp

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
		c = "C2-F:%07d,%07d,%04d,%04d" % (Start_Freq, End_Freq, Amp_Top, Amp_Bottom)
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

	def Enable_Sweep( self ):
		""" Start processing RFE's sweep events
		"""
		self.sweep_active.value = True

	def Disable_Sweep( self ):
		""" Stop processing RFE's sweep events
		"""
		self.sweep_active.value = False

##################################################################################################
# Serial Worker World

	def serial_worker( self ):
		while True:
			cmd = self.recv()
			cmd = cmd[:-2]  # chomp EOL
			if cmd[:2] == '$S':
				#sys.stdout.write('s')
				if self.sweep_active.value == True:
					self.decode_sweep( cmd[2:] )
			elif cmd[:2] == '$D':
				#sys.stdout.write('l')
				self.decode_lcd( cmd[2:] )
			elif cmd[:6] == '#C2-M:':
				#sys.stdout.write('m')
				self.decode_setup( cmd[6:] )
			elif cmd[:6] == '#C2-F:':
				#sys.stdout.write('f')
				self.decode_config( cmd[6:] )
			else:
				#sys.stdout.write('?')
				pass  # ignore faulty reads
			#sys.stdout.flush()

	def decode_setup( self, setupstr ):
		setupfields = ('Main_Model','Expansion_Model','FirmwareVersion')
		setuparray = setupstr.split( ',' )
		sup = dict( zip( setupfields, setuparray ) )

		# Decode fields
		for f in ('Main_Model','Expansion_Model'):
			sup[f] = int( sup[f] )

		main_model = {0:'433M',1:'868M',2:'915M',3:'WSUB1G',4:'2.4G',5:'WSUB3G'}
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

		print self.config
		sys.stdout.flush()

	def decode_lcd( self, lcdstr ):
		mem = []
		for b in lcdstr:
			b = ord(b)
			mem += [b >> i & 1 for i in xrange(7,-1,-1)]
		if len(mem) < 128*64:
			raise Exception( 'truncated display memory packet' )
		lcd = np.zeros( dtype=np.int, shape=(64,128) )
		for y in xrange( 64 ):
			for x in xrange( 128 ):
				p = (y/8)*8*128 + x*8 + (7-y%8)
				lcd[y][x] = mem[p]
		self.lcd_data.put_nowait( lcd )

	def decode_sweep( self, sweepstr ):
		num_steps = ord(sweepstr[0])
		sweep_db = np.array([-float(ord(x))/2.0 for x in sweepstr[1:]])
		sweep_start = 1000 * self.config['Start_Freq']
		sweep_step = self.config['Freq_Step']
		sweep_end = sweep_start + sweep_step * self.config['Sweep_Steps']
		sweep_freq = np.array(range( sweep_start, sweep_end, sweep_step ))
		sweep = ( sweep_freq, sweep_db, (self.config['Amp_Bottom'], self.config['Amp_Top']) )
		#print sweep[1]
		self.sweep_data.put_nowait( sweep )

##################################################################################################

from Tkinter import *
import matplotlib as mpl
mpl.use( 'TkAgg' )
font = {'family' : 'Arial',
        'weight' : 'bold',
        'size'   : 8}
mpl.rc('font', **font)

import matplotlib.pyplot as plt
import matplotlib.image as img
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

class MainWindow( object ):

	sweep_max = None
	sweep_avg = None
	sweep_min = None
	sweep_fstart = 0
	sweep_fstop = 0
	sweep_flen = 0

	def __init__( self, rfe ):
		self.rfe = rfe
		self.sweep_data = self.rfe.sweep_data
		self.lcd_data = self.rfe.lcd_data

		self.application = Tk()
		self.application.wm_title( 'RF Explorer' )		
		self.application.focus_force()
		self.application.protocol( 'WM_DELETE_WINDOW', self.close )

		win = Frame(self.application, bg='gray')
		win.pack(side=LEFT, fill=Y)

		right = Frame(self.application, bg='red', width=400, height=400)
		right.pack(side=RIGHT, fill=BOTH, expand=1)

		frame_a = LabelFrame(win, text='Info', padx=5, pady=5)
		frame_b = LabelFrame(win, text='Sweep control', padx=5, pady=5)
		frame_c = LabelFrame(win, text='Options', padx=5, pady=5)
		frame_a.grid(sticky=E+W)
		frame_b.grid(sticky=E+W)
		frame_c.grid(sticky=E+W)

		for frame in frame_a, frame_b, frame_c:
		    for col in 0, 1, 2:
		        frame.columnconfigure(col, weight=1)

		Label(win, text='Main model:'                ).grid(in_=frame_a, row=0, column=0, sticky=E)
		Label(win, text=self.rfe.config['Main_Model']).grid(in_=frame_a, row=0, column=1, sticky=W)

		Label(win, text='Expansion:'                      ).grid(in_=frame_a, row=1, column=0, sticky=E)
		Label(win, text=self.rfe.config['Expansion_Model']).grid(in_=frame_a, row=1, column=1, sticky=W)

		Label(win, text='Firmware:'                       ).grid(in_=frame_a, row=2, column=0, sticky=E)
		Label(win, text=self.rfe.config['FirmwareVersion']).grid(in_=frame_a, row=2, column=1, sticky=W)

		Label(win, text='f min (kHz):'                  ).grid(in_=frame_a, row=4, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Min_Freq'])).grid(in_=frame_a, row=4, column=1, sticky=W)

		Label(win, text='f max (MHz):'                  ).grid(in_=frame_a, row=5, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Max_Freq'])).grid(in_=frame_a, row=5, column=1, sticky=W)

		Label(win, text='f span (MHz):'                 ).grid(in_=frame_a, row=6, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Max_Span'])).grid(in_=frame_a, row=6, column=1, sticky=W)

		Label(win, text='Sweep steps:'                     ).grid(in_=frame_a, row=3, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Sweep_Steps'])).grid(in_=frame_a, row=3, column=1, sticky=W)

		self.fstart = StringVar()
		self.fstart.set( str(self.rfe.config['Start_Freq']/1000.0) )

		self.fspan = StringVar()
		#self.fspan.set( str(self.rfe.config['Sweep_Steps']*self.rfe.config['Freq_Step']) )
		self.fspan.set( '10.0' )

		self.amptop = StringVar()
		self.amptop.set( str(self.rfe.config['Amp_Top']) )

		self.ampbot = StringVar()
		self.ampbot.set( str(self.rfe.config['Amp_Bottom']) )

		Label(win, text='f start').grid(in_=frame_b, row=0, column=0, sticky=W)
		Entry(win, width=9, textvariable=self.fstart, validate='focusout', vcmd=self.config_entry).grid( in_=frame_b, row=0, column=1, sticky=W)
		Label(win, text='MHz').grid(    in_=frame_b, row=0, column=2, sticky=E)

		Label(win, text='f span').grid(in_=frame_b, row=1, column=0, sticky=W)
		Entry(win, width=9, textvariable=self.fspan, validate='focusout', vcmd=self.config_entry).grid(  in_=frame_b, row=1, column=1, sticky=W)
		Label(win, text='MHz').grid(  in_=frame_b, row=1, column=2, sticky=E)

		Label(win, text='Amp top').grid(in_=frame_b, row=2, column=0, sticky=W)
		Entry(win, width=9, textvariable=self.amptop, validate='focusout', vcmd=self.config_entry).grid( in_=frame_b, row=2, column=1, sticky=W)
		Label(win, text='dB').grid(     in_=frame_b, row=2, column=2, sticky=E)

		Label(win, text='Amp bottom').grid(in_=frame_b, row=3, column=0, sticky=W)
		Entry(win, width=9, textvariable=self.ampbot, validate='focusout', vcmd=self.config_entry).grid( in_=frame_b, row=3, column=1, sticky=W)
		Label(win, text='dB').grid(        in_=frame_b, row=3, column=2, sticky=E)

		self.sweep_val = BooleanVar()
		self.sweep_val.set( rfe.sweep_active.value )
		self.lcddump_val = BooleanVar()
		self.lcddump_val.set( True )
		self.lcddisp_val = BooleanVar()
		self.lcddisp_val.set( True )
		Checkbutton(win, text='Sweep data',  variable=self.sweep_val,   command=self.sweep_check, ).pack(in_=frame_c, anchor=W)
		Checkbutton(win, text='LCD dump',    variable=self.lcddump_val, command=self.lcddump_check).pack(in_=frame_c, anchor=W)
		Checkbutton(win, text='LCD display', variable=self.lcddisp_val, command=self.lcddisp_check).pack(in_=frame_c, anchor=W)

		self.frame = right
		self.figure = mpl.figure.Figure( figsize=(8,6), dpi=100 )
		self.canvas = FigureCanvasTkAgg( self.figure, master=self.frame )

		gs = mpl.gridspec.GridSpec( 3, 1 )
		self.sweep_subplot = self.figure.add_subplot( gs[1:,0] )
		self.lcd_subplot = self.figure.add_subplot( gs[0,0] )

		# style figure
		#self.figure.patch.set_alpha( 0.0 ) # makes background patch invisible
		#self.figure.patch.set_visible( False )
		self.figure.patch.set_color('black')

		# style lcd
		self.lcd_subplot.set_axis_off() # will show graph only, rest is transparent

		# style sweep
		#pself.sweep_subplot.patch.set_alpha( 0.0 )      # makes graph background transparent
		self.sweep_subplot.patch.set_visible( False )  # makes graph background invisible
		self.sweep_subplot.xaxis.grid( color='gray', linestyle='dashed', alpha=0.3 )
		self.sweep_subplot.yaxis.grid( color='gray', linestyle='dashed', alpha=0.3 )
		self.sweep_subplot.set_frame_on( False )  # remove border around graph
		#self.sweep_subplot.spines['bottom'].set_color( 'white' )   # bottom border color (it's off)
		#self.sweep_subplot.spines['top'].set_color( 'white' )      # top border color (it's off)
		#self.sweep_subplot.xaxis.label.set_color( 'white' )        # label color (we have none)
		self.sweep_subplot.tick_params( axis='x', colors='white' )  # ticks and tick labels
		self.sweep_subplot.tick_params( axis='y', colors='white' )  # ticks and tick labels

		#self.img = self.figure.figimage( np.random.random((64*3, 128*3)), cmap='Greys', xo=15, yo=408 )
		self.img = self.lcd_subplot.matshow( np.random.random((64*3, 128*3)), cmap='Greys' )

		self.figure.tight_layout()
		self.canvas.show()
		self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
		self.update()

	def close( self ):
		self.application.quit()
		self.application.destroy()

	def update( self ):
		if not self.sweep_data.empty():
			freq, db, minmax = self.sweep_data.get()
			if len(freq) != len(db):
				return

			if (self.sweep_avg is None) or (freq[0]!=self.sweep_fstart) or (freq[-1]!=self.sweep_fstop) or (len(freq)!=self.sweep_flen):
				self.sweep_max = db
				self.sweep_avg = db
				self.sweep_min = db
				self.sweep_fstart = freq[0]
				self.sweep_fstop = freq[-1]
				self.sweep_flen = len(freq)
				mm = (np.min(self.sweep_min),np.max(self.sweep_max))
				self.sweep_subplot.set_ylim( mm )
				xoff = (self.sweep_fstop - self.sweep_fstart)*0.05
				self.sweep_subplot.set_xlim( (self.sweep_fstart-xoff, self.sweep_fstop+xoff) )
				try:
					self.pminmax.remove()
					self.pavg.remove()
					self.pdb.remove()
				except:
					pass
				self.pminmax = self.sweep_subplot.fill_between( freq, self.sweep_min, self.sweep_max, facecolor='white', alpha=0.1, linewidth=0.2 )
				self.pavg, = self.sweep_subplot.plot( freq, self.sweep_avg, color='red', alpha=0.8, linewidth=1.5 )
				#self.pdb, =  self.sweep_subplot.plot( freq, db, color='#666666', linewidth=0.0, marker='.', alpha=0.5 )
				self.pdb = self.sweep_subplot.fill_between( freq, self.sweep_avg, db, facecolor='#666666', linewidth=0.2, alpha=0.3 )
			else:
				self.sweep_max = np.maximum(self.sweep_max, db)
				self.sweep_min = np.minimum(self.sweep_min, db)
				self.sweep_avg = self.sweep_avg*0.95+db*0.05
				mm = (np.min(self.sweep_min),np.max(self.sweep_max))
				self.sweep_subplot.set_ylim( mm )
				#self.pminmax.set_xdata( freq )
				#self.pminmax.set_ydata( self.sweep_min, self.sweep_max )
				#self.pavg.set_xdata( freq )
				#self.pavg.set_ydata( self.sweep_avg )
				#self.pdb.set_xdata( freq )
				#self.pdb.set_ydata( db )
				self.pminmax.remove()
				self.pminmax = self.sweep_subplot.fill_between( freq, self.sweep_min, self.sweep_max, facecolor='white', alpha=0.1, linewidth=0.2 )
				self.pavg.remove()
				self.pavg, = self.sweep_subplot.plot( freq, self.sweep_avg, color='red', alpha=0.8, linewidth=1.5 )
				self.pdb.remove()
				#self.pdb, =  self.sweep_subplot.plot( freq, db, color='#666666', linewidth=0.0, marker='.', alpha=0.5 )
				self.pdb = self.sweep_subplot.fill_between( freq, self.sweep_avg, db, facecolor='#666666', linewidth=0.2, alpha=0.3 )


			self.canvas.draw()
			self.application.update()	
			#sys.stdout.write('S')
			#sys.stdout.flush()
			# flush queue if we're too slow
			while not self.sweep_data.empty():
				self.sweep_data.get()
		if not self.lcd_data.empty():
			lcd = self.lcd_data.get()
			lcd = np.kron( lcd, np.ones((3,3)) ) # scale by factor 2
			self.img.set_array( lcd )
			self.canvas.draw()
			self.application.update()
			#sys.stdout.write('L')
			#sys.stdout.flush()
			# flush queue if we're too slow
			while not self.lcd_data.empty():
				self.lcd_data.get()
		self.application.after( 10, self.update )

	def mainloop( self ):
		self.application.mainloop()

	def sweep_check( self ):
		if self.sweep_val.get() == True:
			self.rfe.Enable_Sweep()
		else:
			self.rfe.Disable_Sweep()

	def lcddisp_check( self ):
		if self.lcddisp_val.get() == True:
			self.rfe.Enable_LCD()
		else:
			self.rfe.Disable_LCD()

	def lcddump_check( self ):
		if self.lcddump_val.get() == True:
			self.rfe.Enable_DumpScreen()
		else:
			self.rfe.Disable_DumpScreen()

	def config_entry( self ):
		fstart = int(float(self.fstart.get())*1000.0)
		if fstart<self.rfe.config['Min_Freq']:
			return False
		fspan = int(float(self.fspan.get())*1000.0)
		if fspan>self.rfe.config['Max_Span']:
			return False
		fstop = fstart+fspan
		if fstop>self.rfe.config['Max_Freq']:
			return False
		atop = int(self.amptop.get())
		abot = int(self.ampbot.get())
		self.rfe.Current_Config( fstart, fstop,atop, abot )
		return True
