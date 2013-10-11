# -*- coding: utf-8 -*-

from Tkinter import *
from plot import *

class MainWindow( object ):

	def __init__( self, rfe ):
		self.rfe = rfe

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

		Label(win, text='f min (kHz):'                  ).grid(in_=frame_a, row=3, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Min_Freq'])).grid(in_=frame_a, row=3, column=1, sticky=W)

		Label(win, text='f max (MHz):'                  ).grid(in_=frame_a, row=4, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Max_Freq'])).grid(in_=frame_a, row=4, column=1, sticky=W)

		Label(win, text='f span (MHz):'                 ).grid(in_=frame_a, row=5, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Max_Span'])).grid(in_=frame_a, row=5, column=1, sticky=W)

		Label(win, text='Sweep steps:'                     ).grid(in_=frame_a, row=6, column=0, sticky=E)
		Label(win, text=str(self.rfe.config['Sweep_Steps'])).grid(in_=frame_a, row=6, column=1, sticky=W)

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

		self.lcdplot = LcdPlot( self.rfe, frame_d )
		self.sweepplot = SweepPlot( self.rfe, right )

		self.update()

	def close( self ):
		self.application.quit()
		self.application.destroy()

	def update( self ):
		self.lcdplot.update()
		self.sweepplot.update()
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
