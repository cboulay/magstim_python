# coding=latin-1
import serial
import binascii
import Queue
import threading
import time

def _crc(cmd_string):
	#CRC is bit-inverted ( sum ( pieces of cmd_string))
	cmd_sum=0
	for s in cmd_string:
		cmd_sum=cmd_sum+ord(s) #cmd_sum is 213 for '@050'
	return chr(~cmd_sum & 0xff) #for '@050', desired output is Hex: 2A or Str: * or Int: 42

class MagThread(threading.Thread):
	def __init__(self, queue, stimulator):
		threading.Thread.__init__(self)
		self.queue = queue
		self.stimulator = stimulator
		self.alternate_default = True
		
	def run(self):
		while True:
			cmd_string=''
			cmd_hex=''
			data_hex=''
			try:#Get a message from the queue
				msg = self.queue.get(True, 0.5)
			except:#Queue is empty -> Do the default action.
				if isinstance(self.stimulator,Bistim) and self.alternate_default:
					self.alternate_default = False
					self.queue.put({'bistim_mode': 0})
				else:
					self.alternate_default = True
					self.queue.put({'default': 0})
			else:#We got a message
				time_to_sleep = None
				key = msg.keys()[0]
				value = msg[key]
				if key=='trigger': cmd_string='EHr'
				elif key=='arm': cmd_string='EBx' if value else 'EAy'
				elif key=='remocon': cmd_string='Q@n' if value else 'R@m'
				elif key=='stimi':
					cmd_string='@'+str(value).zfill(3)
					cmd_string=cmd_string+_crc(cmd_string)
				elif key=='ignore_safety': cmd_string='b@]'
				elif key=='default': 
					cmd_string='J@u'
					if isinstance(self.stimulator,Rapid2): cmd_string='\@c'
				
				#Bistim specific messages
				elif key=='stimb':
					cmd_string='A'+str(value).zfill(3)
					cmd_string=cmd_string+_crc(cmd_string)
				elif key=='ISI':
					cmd_string='C'+str(value).zfill(3)
					cmd_string=cmd_string+_crc(cmd_string)
				elif key=='bistim_res':
					cmd_string='Y@f' if value else 'Z@e'
					time_to_sleep = 0.1
				elif key=='bistim_mode': cmd_string='X@g'
						
				#Rapid2 specific messages	
				elif key=='train_dur':
					cmd_string='['+str(value).zfill(4)
					cmd_string=cmd_string+_crc(cmd_string)
				elif key=='train_freq':
					cmd_string='B'+str(value).zfill(4)
					cmd_string=cmd_string+_crc(cmd_string)
				elif key=='train_pulses':
					cmd_string='D'+str(value).zfill(5)
					cmd_string=cmd_string+_crc(cmd_string)
				elif key=='shutdown': return
				
				self.stimulator._ser_send_command(cmd_string=cmd_string, cmd_hex=cmd_hex, data_hex=data_hex) #Process the input and send the command
				if time_to_sleep: time.sleep(time_to_sleep)
				self.queue.task_done()#signals to queue job is done. Maybe the stimulator object should do this?
				
#FYI: converting between hex/ascii/bits, often with int in between
#('6E' is hex, 'n' is ascii, and '01101110' is a bit-string)
## TO INT
#hex to int			int('6E',16)=110
#bitstring to int	int('01101110', 2) = 110
#ascii to int		ord('n') = 110
## FROM INT
#int to bitstring	bin(110)[2:].zfill(8) = '01101110'
#int to hex			'%x' % 110 = '6e' OR hex(110) = '0x6e'
#int to ascii		chr(110) = 'n'
## DIRECT HEX <- -> ASCII
#hex to ascii		binascii.unhexlify('6E') = 'n'
#ascii to hex		binascii.hexlify('n') 'n'.encode('hex') = '6e'

#################################################################
### Generic Magstim interface class
### This class allows interaction with a magstim device
### through a serial port. This class should work with either
### Rapid2 or Bistim for single-pulses. It must be subclassed
### (below) for repetitive or double-pulse TMS
###
### Serial triggering is implemented but has indeterminate lag so
### is not recommended. It is possible to import another trigger
### box and .trigger() it when appropriate. In my case I use a
### Caio class which implements .trigger() to use a CONTEC 
### AIO-160802AY-USB to send a TTL through the DAO.
###
### We do not want to block the calling function whenever a
### serial command is issued so this class uses a separate thread
### to work with the serial ports.
###
### The general flow is as follows:
### your program asks or sets for a Magstim attribute value ->
### if getter, return hidden instance attribute value
### if setter, posts a message to the thread ->
### the thread constructs a serial command and passes ->
### to issue the serial command and receives a response ->
### response is parsed to update hidden instance attribute value.
#################################################################
class Magstim(object):
	def __init__(self, port='COM4', trigbox=None):
		"""
		A Magstim (Rapid2 or Bistim) class instance
		allows interaction with a magstim stimulator 
		via serial port.
		Methods:
			magstim_instance.trigger()
				Sends a trigger through the trigbox.
				If trigbox is None, then it uses the serial port.
				
		Properties:
			ready - True if the stimulator reports ready, False otherwise. r
			armed - True if the stimulator reports armed, False otherwise. r
			intensity - The value of the stimulus intensity. rw
			remote_enabled - rw
		"""
		self._stim_remocon= False
		self._stim_ready=False
		self._stim_armed=False
		self._stim_intensity=0
		
		#Initialize the serial port
		self._ser=serial.Serial(port, timeout=0.1)#initialize the serial port
		#The serial port is read with s=ser.read(n_bytes) and written to with ...
		
		self.trigbox=trigbox
		
		#Set thread
		self.q=Queue.Queue()
		
		#Start the thread to handle the queue.
		self.thread = MagThread(self.q, self) #Pass message handler and context.
		self.thread.setDaemon(True) #Dunno, always there in the thread examples.
		self.thread.start() #Kicks off the run(). The thread will check parameters every 0.5 seconds unless another message is passed.
		
		time.sleep(0.1)
		self.remocon=True
		time.sleep(0.1)
		self.q.put({'ignore_safety': 1})
		
		#If this is going to be subclassed, then the subclass MUST define its 
		#specific instance variables before calling the super init, otherwise
		#the thread will communicate with the stimulator, which will return
		#a response, then reading the response will attempt to set instance
		#variables that have yet to be set.
			
	################################
	# PROPERTY GETTERS AND SETTERS #
	################################
	
	# STIMULATOR READY #
	#It isn't necessary to post a message to ask for certain information because the thread
	#automatically requests the stimulator parameters if no other command is waiting.
	def get_stimr(self): return self._stim_ready
	def set_stimr(self, value): pass #read-only
	ready = property(get_stimr, set_stimr)

	# STIMULATOR ARMED #
	def get_stimarm(self): return self._stim_armed or self._stim_ready
	def set_stimarm(self, value): self.q.put({'arm': value}) #Tell the thread to arm/disarm the device
	armed = property(get_stimarm, set_stimarm)
	
	# STIMULATOR REMOTE CONTROL #
	def get_stimremocon(self): return self._stim_remocon
	def set_stimremocon(self, value): self.q.put({'remocon': value}) #Tell the thread to enable/disable remote control.
	remocon = property(get_stimremocon, set_stimremocon)

	# STIMULUS INTENSITY #
	def get_stimi(self): return self._stim_intensity
	def set_stimi(self, value): #Convert the value to the nearest int between 0 and 100
		value=int(round(value))
		value=min(value,100)
		value=max(value,0)
		self.q.put({'stimi': value})#Tell the tread to set the stimulator intensity
	intensity = property(get_stimi, set_stimi)
	
	#FYI
	#See http://docs.python.org/library/functions.html#property
	#and http://docs.python.org/reference/datamodel.html#object.__getattr__ for getters and setters.
	#def __setattr__(self, name, val):
	#	if name != 'x':
	#		self.__dict__[name] = val
	#	else:        
	#		print "%s is read only" % (name)

	###########
	# TRIGGER #
	###########
	def trigger(self):
		if not self.trigbox:
			if not self.remocon: self.remocon = True
			self.q.put({'trigger': 0}) #Can use serial port to trigger magstim but probably not desired because it has an indeterminate lag.
		else: self.trigbox.trigger() #Tell the trigger box to trigger immediately. No messaging.
		self._stim_ready = False #Assume the stimulator is not ready because we just triggered.

	###################
	# SERIAL COMMANDS #
	###################
		
	def _ser_send_command(self, cmd_string=None, cmd_hex='4A', data_hex='40', flush=False):
		if not cmd_string: #Though I don't use the hex, they can be used instead.
			cmd_string=binascii.unhexlify(cmd_hex) + binascii.unhexlify(data_hex)
			cmd_string=cmd_string+_crc(cmd_string)
		#See http://pyserial.sourceforge.net/pyserial_api.html
		self._ser.flushInput()#Clear the response buffer.
		if flush: self._ser.flushOutput()#Should we clear the output buffer? Not sure why we would.
		self._ser.write(cmd_string)#Write to serial port
		time.sleep(0.05)#Introduce a delay to get a response.
		self._ser_get_response()
		
	def _ser_get_response(self):
		#Read from the serial port.
		nchars=self._ser.inWaiting()
		response=self._ser.read(size=nchars)
		#TESTING WITHOUT MAGSTIM#
		#fake_response is J,status,powerA,powerB,pulseint
		#status will be 10001110 = int 142 = 8e = Ž
		#response='JŽ050000000'
		#response='J\x89030030010u'
		#/TESTING#
		
		#All responses contain instrument status
		if bool(nchars):
			if nchars>1:
				#From MSB to LSB: Remocon, Error type, Error present, Replace coil, Coil present, Ready, Armed, Standby
				#.e.g '\t' string == '09' hex == 9 int == '00001001' or, remocon and in standby.
				#e.g. '\x89' string == '89' hex == 137 int ==  '10001001' or, remocon, coil present, and in standby
				#e.g. \x8c' string == '8c' hex == 140 int ==   '10001100' or remocon, coil present, and ready
				#This last example was taken when the coil was armed... so I'm not sure how to get that second bit positive.
				status=ord(response[1])
				#standby=bool(status & 0x1) #(LSB). No point in saving this because it isn't used for anything.
				self._stim_armed=bool(status>>1 & 0x1) #2nd bit
				self._stim_ready=bool(status>>2 & 0x1) #3rd bit
				self._stim_remocon=bool(status>>7 & 0x1) #MSB. Not much point in saving this because it isn't used for anything.
		
			#If the response's first character is hex 4A, then this is a parameter response
			if response[0]=='J' or response[0]=='\\':
				self._stim_intensity=int(response[2:5])#All Magstim parameter responses have Power A
			
			self._parse_response(response)#Further parsing by subclasses
		
	def _parse_response(self, response):
		pass #this will be overshadowed by Bistim or Rapid2 for the extended responses.
	

################
# Bistim Class #
################
class Bistim(Magstim):
	def __init__(self, port='COM4', trigbox=None):
		#Bistim-specific instance variables.
		self._stim_intensityb = 0 #Intensity of B
		self._ISI = 			0 #Double-pulse interval in msec. Float
		self._HR_mode = 		False	#TODO: Use the device response to update this.
		self._master =			True #In Bistim mode and the device is being used to control the stim timing.
		Magstim.__init__(self, port=port, trigbox=trigbox)#Call the super init (which also inits the thread)
		
	def __del__(self):
		self.ISI = 0
		self.intensityb = 0
		
	# STIMULUS INTENSITY  B #
	def get_stimb(self):
		return self._stim_intensityb
	def set_stimb(self, value): #Convert the value to the nearest int between 0 and 100
		value=int(round(value))
		value=min(value,100)
		value=max(value,1)#Stim intensity of 0 screws up the threading.
		self.q.put({'stimb': value})#Tell the tread to set the stimulator intensity
	intensityb = property(get_stimb, set_stimb)
	
	# Double-pulse ISI #
	def get_isi(self):
		return self._ISI
	def set_isi(self, value):
		#Sanity check the ISI
		value=max(value,0.0)#TODO: What is the minimum ISI?
		value=min(value,999.0)#TODO: What is the maximum ISI?
		if (value % 1.0) > 0.0 and value < 100:#If the ISI has a decimal value, be sure to set the stimulator to HR mode
			if not self.hr_mode:
				self.hr_mode=True #Note that setting the stimulator to hr_mode should only be done 100's of ms after remote_control
				time.sleep(0.1)
			self.q.put({'ISI': int(value*10)})
		else:
			if self.hr_mode:
				self.hr_mode=False
				time.sleep(0.1)
			self.q.put({'ISI': int(value)})
	ISI = property(get_isi, set_isi)
	
	# ISI HR MODE #
	def get_hr_mode(self):
		return self._HR_mode
	def set_hr_mode(self, value):
		self.q.put({'bistim_res': value})
	hr_mode = property(get_hr_mode, set_hr_mode)
	
	# MASTER MODE #
	def get_master_mode(self):
		return self._master
	def set_master_mode(self, value): pass #read-only
	master_mode = property(get_master_mode, set_master_mode)
	
	########################################
	# Bistim-specific serial port commands #
	########################################
	def _parse_response(self, response):
		#'J\t030030010\xf5'
		#'X\t4j'
		#Read the parts of the parameter response that are specific to Bistim
		if response[0]=='J' or response[0]=='\\':
			if len(response)>=7: self._stim_intensityb=int(response[5:8])
			if len(response)>=10: self._ISI= (float(response[8:11]))/10 if self.hr_mode else float(response[8:11])
		elif response[0]=='X':
			mode=response[2]
			mode_hex=binascii.hexlify(mode)
			self._master = bool(mode_hex[0]=='3') #If the code starts with a 3, it is master. If it is 5, it is slave
			self._HR_mode = bool(mode_hex[1]=='4') #0 is single, 1=simul, 2=lowres, 3=extern, 4=hires
			
################
# Rapid2 Class #
################
#I don't have a Rapid2 to test against so this class might not work.
#!!!!! I DO NOT CALCULATE THE TOTAL ENERGY DISSIPATION
#!!!!! SEE THE PDF TO MAKE SURE YOUR STIMULUS PARAMETERS
#!!!!! WILL YIELD EXPECTED RESULTS
class Rapid2(Magstim):
	def __init__(self, port='COM4', triggerbox=None):
		#Rapid2-specific instance variables.
		self._train_dur = 0		#How long the stimulus train lasts
		self._train_freq = 0	#Pulse frequency, in Hz
		self._train_pulses = 0	#Number of pulses in the train
		Magstim.__init__(self, port=port, triggerbox=triggerbox)#Call the super init (which also inits the thread)
		
	# Train Duration #
	def get_train_dur(self): return self._train_dur
	def set_train_dur(self, value):
		value=int(round(10*value))
		self.q.put({'train_dur': value})
	train_duration = property(get_train_dur, set_train_dur)
	
	# Train Frequency #
	def get_train_freq(self): return self._train_freq
	def set_train_freq(self, value): 
		value=int(round(10*value))
		self.q.put({'train_freq': value})
	train_frequency = property(get_train_freq, set_train_freq)
	
	# Train Pulses #
	def get_train_pulses(self): return self._train_pulses
	def set_train_pulses(self, value): 
		#sanitize the number of pulses
		value=int(round(value))
		self.q.put({'train_pulses': value})
	train_pulses = property(get_train_pulses, set_train_pulses)
	
	####################################
	# Rapid2-specific response parsing #
	####################################
	def _parse_response(self, response):
		#Read the parts of the parameter response that are specific to Rapid2
		if response[0]=='J' or response[0]=='\\':
			if len(response)>=8: self._train_freq=(float(response[5:9]))/10
			if len(response)>=13: self._train_pulses=int(response[9:14])
			if len(response)>=17: self._train_duration=(float(reponse[14:18]))/10
			if len(response)>=21: self._train_wait_time=(float(response[18:22]))/10