#Python interface for Magstim TMS devices

Depends on pyserial.

Uses threading.

Tested with Bistim for single-pulse only. Not tested with Rapid2.

[Instructions to make a serial cable](http://www.psych.usyd.edu.au/tmslab/downloads/SerialCable_and_Rapid2Toolbox_v1.pdf)

### Information not in the pdfs


<table>
<tr><td>Host Command</td></tr>
<tr><td>D7</td><td>D6</td><td>D5</td><td>D4</td><td>D3</td><td>D2</td><td>D1</td><td>D0</td><td>Hex</td><td>Description</td></tr>
<tr><td>0</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>58</td><td>Command</td></tr>
<tr><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>40</td><td>Padding Byte</td></tr>
<tr><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>67</td><td>CRC</td></tr>
<tr><td>Base Controller Response</td></tr>
<tr><td>0</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>58</td><td>Command Acknowledge</td></tr>
<tr><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>NN</td><td>Instrument Status</td></tr>
<tr><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>NN</td><td>Current System Mode (see section below)</td></tr>
<tr><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>N</td><td>NN</td><td>CRC</td></tr>
</table>

Possible Return Values of Current System Mode:

<table>
<tr><td>Value (hexadecimal)</td><td>Description</td></tr>
<tr><td>30</td><td>System operating as a single stimulator.</td></tr>
<tr><td>31</td><td>System operating as master in simultaneous firing mode.</td></tr>
<tr><td>32</td><td>System operating as master in normal BISTIM mode with low resolution time setting mode active.</td></tr>
<tr><td>33</td><td>System operating as master in BISTIM mode with independent external triggering for master and slave enabled.</td></tr>
<tr><td>34</td><td>System operating as master in normal BISTIM mode with high resolution time setting mode active.</td></tr>
<tr><td>51</td><td>System operating as slave in simultaneous firing mode.</td></tr>
<tr><td>52</td><td>System operating as slave in normal BISTIM mode with low resolution time setting mode active.</td></tr>
<tr><td>53</td><td>System operating as slave in BISTIM mode with independent external triggering for master and slave enabled.</td></tr>
<tr><td>54</td><td>System operating as slave in normal BISTIM mode with high resolution time setting mode active.</td></tr>
</table>