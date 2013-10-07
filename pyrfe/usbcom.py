#!/usr/bin/env python
# -*- coding: utf-8 -*-

#http://www.beyondlogic.org/usbnutshell/usb1.shtml

import usb
import array

dev = None
cfg = None
intf = None
epin = None
epout = None

def find():
    """Returns list of usb device objects of all connected RF-Explorers.
    """
    return usb.core.find( find_all=True, idVendor=0x10c4, idProduct=0xea60 )

def connect( cid=0 ):
    """Connects to the RF-Explorer in the system numbered by device.
       Returns True if successfull, else False.
    """
    global dev, cfg, intf, epin, epout

    # TODO: this should not be a global singleton
    dev = usb.core.find( find_all=True, idVendor=0x10c4, idProduct=0xea60 )[cid]
    if not dev:
      return False

    # use default config
    dev.set_configuration()

    # so far it has always been like this on my hp50g  
    assert( dev.bLength == 18 )
    assert( dev.bDescriptorType == 1 )
    assert( dev.bDeviceClass == 0 )
    assert( dev.bDeviceProtocol == 0 )
    assert( dev.bDeviceSubClass == 0 )
    assert( dev.bNumConfigurations == 1 )

    # get an endpoint instance
    cfg = dev.get_active_configuration()

    # so far it has always been like this on my RF-Explorer
    assert( cfg.bNumInterfaces == 1 )

    intf = cfg[(0,0)] # (interface index, altsetting index)

    # so far it has always been like this on my RF-Explorer
    assert( intf.bInterfaceNumber == 0 )
    assert( intf.bAlternateSetting == 0 )

    # not required with just one alt setting
    #intf.set_altsetting()

    # so far it has always been like this on my RF-Explorer
    assert( intf.bNumEndpoints == 2 )

    # hardcoded assumption. should filter for in/out
    epin = intf[0]
    epout = intf[1]

    # so far it has always been like this on my RF-Explorer
    assert( usb.util.endpoint_direction( epin.bEndpointAddress ) == usb.util.ENDPOINT_IN )
    assert( usb.util.endpoint_type( epin.bEndpointAddress ) == usb.util.ENDPOINT_TYPE_ISO )
    assert( usb.util.endpoint_direction( epout.bEndpointAddress ) == usb.util.ENDPOINT_OUT )
    assert( usb.util.endpoint_type( epout.bEndpointAddress ) == usb.util.ENDPOINT_TYPE_ISO )
    assert( epin.bEndpointAddress == 129 ) # srsly?
    assert( epout.bEndpointAddress == 1 )

    return True

def write( data, timeout=1000 ):
    """Sends data to RF-Explorer. data can be a string or array.
       Returns the number of bytes written.
    """ 
    global epout
    return epout.write( data, timeout=timeout )

def read( length=0, timeout=1000, until=False ):
    """Reads length bytes of data from the RF-Explorer and returns them as
       array.array of bytes.
    """
    global epin
    inp = array.array( 'B' )
    if until==False:
      if length == 0:
        inp += epin.read( 1024, timeout=timeout )
      else:
        while len( inp ) < length:
          inp += epin.read( length-len(inp), timeout=timeout )
    else:
      inp += epin.read( epin.wMaxPacketSize, timeout=timeout )
      while inp[-1] != until:
        inp += epin.read( epin.wMaxPacketSize, timeout=timeout )
    return inp

def reset():
    """Resets USB state.
    """
    global dev
    dev.reset()

def flush( all=False, timeout=100 ):
    """Flushes the input buffer.
    """
    inp = array( 'B' )
    while all:
      try:
        inp += read( epin.wMaxPacketSize*16, timeout=timeout )
      except:
        break
    return inp
