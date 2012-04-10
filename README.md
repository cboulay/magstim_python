#Python interface for Magstim TMS devices

## Instructions
Be sure you have pyserial installed.

```python

#Import your stimulator class
from Magstim.MagstimInterface import Magstim, Bistim, Rapid2
#Define your serial port
serPort='COM6'
#If using an additional device to do the triggering (highly recommended), try this
from Caio.TriggerBox import TTL
stimulator=Bistim(port=serPort, trigbox=TTL())
#Else if using the serial port to trigger (note: indeterminate lag/jitter!)
stimulator=Magstim(port=serPort)

#The following functions and attributes are now available to you.
stimulator.armed #rw. Pass True to arm before triggering.
stimulator.trigger()
stimulator.ready #read-only
stimulator.remocon #read-write. Pass True to enable. Should be enabled by default on stimulator init.
stimulator.intensity #rw. Pass int value to change stimulator intensity.
#Bistim-only
stimulator.intensityb
stimulator.ISI
stimulator.hr_mode #Whether or not bi-stim is in high-res mode. High-res automatic if ISI is decimal.
stimulator.master_mode #read-only. This device is controlling timing.
#Rapid2 only
stimulator.train_duration #How long the stimulus train lasts in secs
stimulator.train_frequency #Pulse frequency, in Hz
stimulator.train_pulses #Number of pulses in the train
```

## Other information

* You will not receive an error if there is no magstim device connected, but the stimulator parameters should return False

* Tested with Bistim for single-pulse only. Not tested with Rapid2.

* [Instructions to make a serial cable](http://www.psych.usyd.edu.au/tmslab/downloads/SerialCable_and_Rapid2Toolbox_v1.pdf)

* Uses my [caio module](https://github.com/cboulay/caio-python)

* Information not in the pdfs:

<table>
<tr><td colspan="10">Host Command</td></tr>
<tr><th>D7</th><th>D6</th><th>D5</th><th>D4</th><th>D3</th><th>D2</th><th>D1</th><th>D0</th><th>Hex</th><th>Description</th></tr>
<tr><td>0</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>58</td><td>Command</td></tr>
<tr><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>40</td><td>Padding Byte</td></tr>
<tr><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>67</td><td>CRC</td></tr>
<tr><td colspan="10">Base Controller Response</td></tr>
<tr><td>0</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>58</td><td>Command Acknowledge</td></tr>
<tr><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>NN</td><td>Instrument Status</td></tr>
<tr><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>NN</td><td>Current System Mode (see section below)</td></tr>
<tr><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>NN</td><td>CRC</td></tr>
</table>

Possible Return Values of Current System Mode:

<table>
<tr><th>Value (hexadecimal)</th><th>Value (string)</th><th>Description</th></tr>
<tr><td>30</td><td>0</td><td>System operating as a single stimulator.</td></tr>
<tr><td>31</td><td>1</td><td>System operating as master in simultaneous firing mode.</td></tr>
<tr><td>32</td><td>2</td><td>System operating as master in normal BISTIM mode with low resolution time setting mode active.</td></tr>
<tr><td>33</td><td>3</td><td>System operating as master in BISTIM mode with independent external triggering for master and slave enabled.</td></tr>
<tr><td>34</td><td>4</td><td>System operating as master in normal BISTIM mode with high resolution time setting mode active.</td></tr>
<tr><td>51</td><td>Q</td><td>System operating as slave in simultaneous firing mode.</td></tr>
<tr><td>52</td><td>R</td><td>System operating as slave in normal BISTIM mode with low resolution time setting mode active.</td></tr>
<tr><td>53</td><td>S</td><td>System operating as slave in BISTIM mode with independent external triggering for master and slave enabled.</td></tr>
<tr><td>54</td><td>T</td><td>System operating as slave in normal BISTIM mode with high resolution time setting mode active.</td></tr>
</table>