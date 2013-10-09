#!/usr/bin/env python

import signal
import sys
import pyrfe
from IPython import embed
import time

def graceful_exit( signal, frame ):
	print "bye!"
	rfe.stop()
	win.close()
	sys.exit( 0 )

rfe = pyrfe.rfe.RFE( '/dev/tty.SLAB_USBtoUART' )
win = pyrfe.rfe.MainWindow( rfe.sweep_data, rfe.lcd_data )

while len(rfe.config) == 0:
	time.sleep(0.05)
print rfe.config
rfe.Enable_DumpScreen()
rfe.Enable_Sweep()

signal.signal( signal.SIGINT, graceful_exit )
signal.signal( signal.SIGTERM, graceful_exit )

#embed()
win.mainloop()

rfe.stop()