#!/usr/bin/env python

import signal
import sys
import pyrfe
from IPython import embed

def graceful_exit( signal, frame ):
	print "bye!"
	rfe.stop()
	sys.exit( 0 )

rfe = pyrfe.rfe.RFE( '/dev/tty.SLAB_USBtoUART' )

signal.signal( signal.SIGINT, graceful_exit )
signal.signal( signal.SIGTERM, graceful_exit )

embed()

rfe.stop()
