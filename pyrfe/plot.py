# -*- coding: utf-8 -*-

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

import Tkinter as tk

class LcdPlot( object ):

	def __init__( self, rfe, frame ):
		self.rfe = rfe
		self.frame = frame
		self.lcd_data = self.rfe.lcd_data

		self.figure_lcd = mpl.figure.Figure( figsize=(2,1), dpi=100, frameon=False )
		self.canvas_lcd = FigureCanvasTkAgg( self.figure_lcd, master=self.frame )
		self.lcd_subplot = self.figure_lcd.add_subplot( '111' )

		# style figure
		self.figure_lcd.patch.set_alpha( 0.0 ) # makes background patch invisible
		self.figure_lcd.patch.set_visible( False )

		# style lcd
		self.lcd_subplot.set_axis_off() # will show graph only, rest is transparent

		self.img = self.lcd_subplot.matshow( np.random.random((64*2, 128*2)), cmap='Greys' ) # why does only random work, not zeros or ones?

		#self.figure_lcd.tight_layout()
		self.canvas_lcd.show()
		self.canvas_lcd.get_tk_widget().grid()

	def update( self ):
		if not self.lcd_data.empty():
			while not self.lcd_data.empty():
				lcd = self.lcd_data.get()
			lcd = np.kron( lcd, np.ones((2,2)) ) # scale by factor 2
			self.img.set_array( lcd )
			self.canvas_lcd.draw()


class SweepPlot( object ):

	sweep_max = None
	sweep_avg = None
	sweep_min = None
	sweep_fstart = 0
	sweep_fstop = 0
	sweep_flen = 0

	def __init__( self, rfe, frame ):
		self.rfe = rfe
		self.frame = frame
		self.sweep_data = self.rfe.sweep_data

		self.figure = mpl.figure.Figure( figsize=(8,6), dpi=100 )
		self.canvas = FigureCanvasTkAgg( self.figure, master=self.frame )
		self.sweep_subplot = self.figure.add_subplot( '111' )

		# style figure
		self.figure.patch.set_color('black')

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
		self.sweep_subplot.xaxis.get_major_formatter().set_scientific( False )

		self.figure.tight_layout()
		self.canvas.show()
		self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

	def update( self ):
		if not self.sweep_data.empty():
			# flush queue if we're too slow
			while not self.sweep_data.empty():
				freq, db, minmax = self.sweep_data.get()

			if len(freq) != len(db):
				print 'freq/db length mismatch'
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
