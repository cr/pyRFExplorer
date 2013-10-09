# RX-Explorer RS232 Interface
# http://code.google.com/p/rfexplorer/wiki/RFExplorerRS232Interface

#import usbcom as com
import ttycom as com
import array

def to_ascii( value, digits, binary=False ):
	if binary:
		b = bin(value)[2:]
		b = '0'*(digits-len(b))+b
		return b
	else:
		return ("%0"+digits+"d") % value

def from_ascii( s, binary=False ):
	if binary:
		raise Exception('not implemented yet')
	else:
		return int(s)

def init():
	com.connect()

def send( command ):
	l = len( command )
	if l>62:
		raise Exception( 'command is longer than 62+2 bytes' )
	c = "#%c%s" % (chr(len(command)+2), command)
	com.write( c )

def recv():
	return com.read( until="\r\n" )

def Current_Config( Start_Freq, End_Freq, Amp_Top, Amp_Bottom ):
	""" Send current Spectrum Analyzer configuration data.
	    It will change current configuration for RFE.
	"""
	c = "C2-F:%s,%s,%s,%s" % (Start_Freq, End_Freq, Amp_Top, Amp_Bottom)
	send( c )

def Request_Config():
	""" Request RFE to send Current_Config
	"""
	c = "C0"
	send( c )

	setupstr = recv()
	configstr = recv()

	print repr(setupstr)
	print repr(configstr)

	if setupstr[:6] != "#C2-M:":
		raise Exception( 'received unexpected setup packet' )
	if configstr[:6] != "#C2-F:":
		raise Exception( 'received unexpected config packet' )

	setupfields = ('Main_Model','Expansion_Model','FirmwareVersion')
	setuparray = setupstr[7:].split( ',' )
	setupdict = dict( zip( setupfields, setuparray ) )

	configfields = ('Start_Freq','Freq_Step','Amp_Top','Amp_Bottom','Sweep_Steps',
		'ExpModuleActive','CurrentMode','Min_Freq','Max_Freq','Max_Span','RBW')
	configarray = configstr[7:].split( ',' )
	if len(configarray) == len(configfields)-1:
		configarray.append( '-1' )  # Firmware version 1.08 or older
	if len(configarray) != len(configfields):
		raise Exception( 'received unexpected number of config values' )
	configdict = dict( zip( configfields, configarray ) )

	cfg = dict(setupdict.items() + configdict.items())



	# Decode fields
	for f in configfields + ('Main_Model','Expansion_Model'):
		cfg[f] = int( cfg[f] )

	cfg['ExpModuleActive'] = cfg['ExpModuleActive'] == 1

	main_model = {0:'433M',1:'868M',2:'915M',3:'WSUSB1G',4:'2.4G',5:'WSUSB3G'}
	cfg['Main_Model'] = main_model[cfg['Main_Model']]

	expansion_model = {0:'433M',1:'868M',2:'915M',3:'WSUB1G',4:'2.4G',5:'WSUB3G', 255:''}
	cfg['Expansion_Model'] = expansion_model[cfg['Expansion_Model']]

	current_mode = {0:'SPECTRUM_ANALYZER',1:'RF_GENERATOR',2:'WIFI_ANALYZER',255:'UNKNOWN'}
	cfg['CurrentMode'] = current_mode[cfg['CurrentMode']]


	return cfg


def Request_Hold():
	""" Stop spectrum analyzer data dump
	"""
	c = "CH"
	return send( c )

def Request_Shutdown():
	""" Shutdown RF Explorer unit
	"""
	c = "CS"
	return send( c )

def Enable_DumpScreen():
	""" Request RFE to dump all screen data. It will remain active until
	    Disable_DumpScreen is sent. 
	"""
	c = "D1"
	return send( c )

def Disable_DumpScreen():
	""" Request RFE to stop dumping screen data
	"""
	c = "D0"
	return send( c )

def Change_Baudrate( baudrate ):
	""" Switch RF Explorer communication baudrate. The switch is immediate and it is
	    lost after a reset. Reliable and recommended communication baudrates are 2400bps
	    and 500Kbps only.
	    Codified baudrate values are: 0-500Kbps, 1-1200bps, 2-2400bps,
	    3-4800bps, 4-9600bps, 5-19200bps, 6-38400bps, 7-57600bps, 8-115200bps
	"""
	c = "Cc%s" % baudrate
	return send( c )

def Disable_LCD():
	""" Request RFE to switch LCD OFF and stop all draw activity
	"""
	c = "L0"
	return send( c )

def Enable_LCD():
	""" Request RFE to switch LCD back ON and resume all draw activity
	"""
	c = "L1"
	return send( c )