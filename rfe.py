#!/usr/bin/env python

import signal
import sys
from pyrfe import *
from IPython import embed

def graceful_exit( signal, frame ):
	print "Shutting down RFE...",
	r.Disable_DumpScreen()
	r.Disable_Sweep()
	r.Enable_LCD()
	r.stop()
	g.close()
	print 'bye!'
	sys.exit( 0 )

r = rfe.RFE( '/dev/tty.SLAB_USBtoUART' )
r.Disable_DumpScreen()
r.Disable_LCD()
r.Enable_Sweep()

g = gui.MainWindow( r )

signal.signal( signal.SIGINT, graceful_exit )
signal.signal( signal.SIGTERM, graceful_exit )

#embed()
g.mainloop()

r.Disable_DumpScreen()
r.Enable_LCD()
r.stop()