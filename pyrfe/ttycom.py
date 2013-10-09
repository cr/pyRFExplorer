# -*- coding: utf-8 -*-

import serial

dev = None

def find():
    """Returns list of serial device objects that might be RF-Explorers.
    """
    return ['/dev/tty.SLAB_USBtoUART']

def connect( cid=0 ):
    """Connects to the RF-Explorer in the system numbered by device.
       Returns True if successfull, else False.
    """
    global dev
    dev = serial.Serial( find()[cid] )
    dev.baudrate = 500000
    dev.timeout = 1.0
    return True

def write( data, timeout=1000 ):
    """Sends data to RF-Explorer. Data can be a string or array.
       Returns the number of bytes written.
    """ 
    global dev
    dev.timeout = timeout/1000.0
    return dev.write( data )

def read( length=0, timeout=1000, until=False ):
    """Reads length bytes of data from the RF-Explorer and returns them
       as string.
    """
    global dev
    dev.timeout = timeout/1000.0
    inp = ""
    if until==False:
      if length == 0:
        inp += dev.read()
      else:
      	inp += dev.read( length )
    else:
      inp += dev.read( 2 )
      while inp[-2:] != until:
        inp += dev.read()
    return inp

def reset():
    """Resets Serial state.
    """
    global dev
    raise Exception( 'reset() is not implemented' )

def flush( all=False, timeout=100 ):
    """Flushes the input buffer.
    """
    inp = ""
    while all:
      try:
        inp += read( 1024, timeout=timeout  )
      except:
        break
    return inp
