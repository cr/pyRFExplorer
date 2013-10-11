# -*- coding: utf-8 -*-


from Tkinter import *
import numpy as np
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

		win = Frame(self.application, bg='white')
		win.pack(side=LEFT, fill=Y)

		right = Frame(self.application, bg='black', width=400, height=400)
		right.pack(side=RIGHT, fill=BOTH, expand=1)

		frame_a = LabelFrame(win, text='Info', padx=5, pady=5)
		frame_b = LabelFrame(win, text='Sweep control', padx=5, pady=5)
		frame_c = LabelFrame(win, text='Options', padx=5, pady=5)
		frame_d = Frame( win, padx=0, pady=0 )
		frame_a.grid(sticky=E+W)
		frame_b.grid(sticky=E+W)
		frame_c.grid(sticky=E+W)
		frame_d.grid(sticky=E+W)

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
		self.fstart.set( str(self.rfe.config['Start_Freq']/1e3) )

		self.fspan = StringVar()
		fspan = self.rfe.config['Sweep_Steps']*self.rfe.config['Freq_Step']
		fspan = 1e3*round(fspan/1e3)/1e6
		self.fspan.set( str(fspan) )

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
		self.lcddump_val.set( False )
		self.lcddisp_val = BooleanVar()
		self.lcddisp_val.set( False )
		Checkbutton(win, text='Sweep data',  variable=self.sweep_val,   command=self.sweep_check, ).pack(in_=frame_c, anchor=W)
		Checkbutton(win, text='LCD dump',    variable=self.lcddump_val, command=self.lcddump_check).pack(in_=frame_c, anchor=W)
		Checkbutton(win, text='LCD display', variable=self.lcddisp_val, command=self.lcddisp_check).pack(in_=frame_c, anchor=W)

		self.frame = right
		self.figure = mpl.figure.Figure( figsize=(8,6), dpi=100 )
		self.canvas = FigureCanvasTkAgg( self.figure, master=self.frame )
		self.figure_lcd = mpl.figure.Figure( figsize=(2,1), dpi=100, frameon=False )
		self.canvas_lcd = FigureCanvasTkAgg( self.figure_lcd, master=frame_d )

		#gs = mpl.gridspec.GridSpec( 3, 1 )
		#self.sweep_subplot = self.figure.add_subplot( gs[1:,0] )
		#self.lcd_subplot = self.figure.add_subplot( gs[0,0] )
		self.sweep_subplot = self.figure.add_subplot( '111' )
		self.lcd_subplot = self.figure_lcd.add_subplot( '111' )

		# style figure
		self.figure_lcd.patch.set_alpha( 0.0 ) # makes background patch invisible
		self.figure_lcd.patch.set_visible( False )
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

		#self.img = self.figure.figimage( np.random.random((64*1, 128*1)), cmap='Greys', xo=0, yo=0 )
		#self.img = self.lcd_subplot.matshow( np.random.random((64*2, 128*2)), cmap='Greys' )
		self.img = self.lcd_subplot.matshow( np.random.random((64*2, 128*2)), cmap='Greys' ) # why does only random work, not zeros or ones?

		self.figure.tight_layout()
		self.canvas.show()
		self.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

		#self.figure_lcd.tight_layout()
		self.canvas_lcd.show()
		self.canvas_lcd.get_tk_widget().grid()
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
			lcd = np.kron( lcd, np.ones((2,2)) ) # scale by factor 2
			self.img.set_array( lcd )
			#self.canvas.draw()
			self.canvas_lcd.draw()
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
