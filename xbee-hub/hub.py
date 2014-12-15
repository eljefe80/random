#! /usr/bin/python
# This is the an implementation of controlling the Lowe's Iris Smart
# Switch.  It will join with a switch and allow you to control the switch
#
#  Only ONE switch though.  This implementation is a direct port of the 
# work I did for an Arduino and illustrates what needs to be done for the 
# basic operation of the switch.  If you want more than one switch, you can
# adapt this code, or use the ideas in it to make your own control software.
#
# Have fun

from xbee import ZigBee,XBee 
from apscheduler.scheduler import Scheduler
from cherrypy.process import plugins
import logging
import datetime
import time
import serial
import sys
import shlex
import dataset
from uuid import uuid4
import cherrypy
import pprint
import binascii
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import cStringIO
import urllib
import os

HEADER_FILE='header.inc'
FOOTER_FILE='footer.inc'

#from http.client import HTTPResponse
#-------------------------------------------------
# the database where I'm storing stuff
DATABASE='xbee.db'

# on the Raspberry Pi the serial port is ttyAMA0
XBEEPORT = '/dev/ttyAMA0'
XBEEBAUD_RATE = 9600

# The XBee addresses I'm dealing with
BROADCAST = '\x00\x00\x00\x00\x00\x00\xff\xff'
UNKNOWN = '\xff\xfe' # This is the 'I don't know' 16 bit address

switchLongAddr = '12'
switchShortAddr = '12'

global zb
global ser

#-------------------------------------------------
logging.basicConfig()

#------------ XBee Stuff -------------------------
# Open serial port for use by the XBee
nodeTypes = {
 0x1c: "Smart Plug Switch",
 0x1f: "Door/Window Contact Sensor",
    }

def getAllNodes():
    return endpoint_table.all()

def getNode(source_addr_long,source_addr):
    return endpoint_table.find_one(source_addr_long,source_addr)

def getNodeByID(id):
    types = endpoint_data.distinct('type',node_id=id)
    return dict(id=id,types=types)

def getAxes(id, type):
    data = endpoint_data.find(node_id=id,type=type)
    i = 0
    x = []
    y = []
    for events in data:
	x.append( datetime.datetime.fromtimestamp(events['time']))
	y.append(events['value'])
	i = i+1
    return dict(x=x,y=y)
#    return x

def getLatestCheckIn(id):
    timestamp = endpoint_data.find(node_id=id,order_by='-id',_limit=1)
    ts = 0
    for i in timestamp:
	ts = i['time']
    return ts

def nextId():
    id = meta_table.find_one(name='id')
    if id is None:
	value = 0
    else:
	value = meta_table.find_one('id')['value']
    data = dict(name='id', value=value+1)
    meta_table.upsert(data,['name'])
    return id 

def srcToID(source_addr_long):
    endpoint = endpoint_table.find_one(source_addr_long=binascii.hexlify(source_addr_long),source_addr=binascii.hexlify(source_addr))
    if endpoint is None:
	print 'Something BAD has happened'
	return
    else:
	return endpoint['id']

def manageClient(source_addr_long):
    endpoint = endpoint_table.find_one(source_addr_long=binascii.hexlify(source_addr_long))
    if endpoint is not None:
	return endpoint['id']
    else:
	uuid=binascii.hexlify(uuid4().bytes)
#	id = nextId()
	data = dict(source_addr_long=binascii.hexlify(source_addr_long), uuid=uuid)
	endpoint_table.insert(data)
	return endpoint_table.find_one(uuid=uuid)['id']

def checkStateAll():
    endpoint = endpoint_table.all()
    for node in endpoint:
	checkState(node['id'])

def checkState(id):
    node = endpoint_table.find_one(id=id)
    databytes = '\x01'
    sendSwitch( binascii.unhexlify(node['source_addr_long']),
#	binascii.unhexlify(node['source_addr'])
	'\xff\xfe', '\x00',
	'\x02', '\x00\xee', '\xc2\x16', '\x01', databytes)


        # Turn Switch Off
#        if(str1[0] == '0'):
#            print 'Turn switch off'
#            databytes1 = '\x01'
#            databytesOff = '\x00\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xee', '\xc2\x16', '\x01', databytes1)
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xee', '\xc2\x16', '\x02', databytesOff)
        # Turn Switch On
#        if(str1[0] == '1'):
#            print 'Turn switch on'
#            databytes1 = '\x01'
#            databytesOn = '\x01\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xee', '\xc2\x16', '\x01', databytes1)
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xee', '\xc2\x16', '\x02', databytesOn)
        # this goes down to the test routine for further hacking
#        elif (str1[0] == '2'):
            #testCommand()
#            print 'Not Implemented'
        # This will get the Version Data, it's a combination of data and text
#        elif (str1[0] == '3'):
#            print 'Version Data'
#            databytes = '\x00\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xf6', '\xc2\x16', '\xfc', databytes)
        # This command causes a message return holding the state of the switch
#        elif (str1[0] == '4'):
##            print 'Switch Status'
        # restore normal mode after one of the mode changess that follow
#        elif (str1[0] == '5'):
#            print 'Restore Normal Mode'
#            databytes = '\x00\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xf0', '\xc2\x16', '\xfa', databytes)
        # range test - periodic double blink, no control, sends RSSI, no remote control
        # remote control works
#        elif (str1[0] == '6'):
#            print 'Range Test'
#            databytes = '\x01\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xf0', '\xc2\x16', '\xfa', databytes)
        # locked mode - switch can't be controlled locally, no periodic data
#        elif (str1[0] == '7'):
#            print 'Locked Mode'
#            databytes = '\x02\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xf0', '\xc2\x16', '\xfa', databytes)
        # Silent mode, no periodic data, but switch is controllable locally
#        elif (str1[0] == '8'):
#            print 'Silent Mode'
#            databytes = '\x03\x01'
#            sendSwitch(switchLongAddr, switchShortAddr, '\x00', '\x02', '\x00\xf0', '\xc2\x16', '\xfa', databytes)


#def logCheckIn(uuid, data):

# this is a call back function.  When a message
# comes in this function will get the data
def messageReceived(data):
#   print 'gotta packet' 
#   print data
    # This is a test program, so use global variables and
    # save the addresses so they can be used later
    #global switchLongAddr
    #global switchShortAddr

#    if (data['name'] == "tx_status)
    if (data['id'] == "at_response"):
        pprint.pprint(data)
	return
#    print 'Received message type: ' + data['name']
    if (data['id'] == 'status'):
        pprint.pprint(data)
	return
    switchLongAddr = data['source_addr_long'] 
    switchShortAddr = data['source_addr']
    id = manageClient(switchLongAddr)
    if id > 1:
     print 'Received message from uuid: ' + str(id)
    clusterId = (ord(data['cluster'][0])*256) + ord(data['cluster'][1])
#    time = int(datetime.datetime.now().time())
    info = dict(node_id = id, time = time.time())
    endpoint_state.upsert(info,['id'])
 #   print 'Cluster ID:', hex(clusterId),
    if (clusterId == 0x13):
        # This is the device announce message.
        # due to timing problems with the switch itself, I don't 
        # respond to this message, I save the response for later after the
        # Match Descriptor request comes in.  You'll see it down below.
        # if you want to see the data that came in with this message, just
        # uncomment the 'print data' comment up above
        print 'Device Announce Message'
	pprint.pprint(data)
    elif (clusterId == 0x8005):
        # this is the Active Endpoint Response This message tells you
        # what the device can do, but it isn't constructed correctly to match 
        # what the switch can do according to the spec.  This is another 
        # message that gets it's response after I receive the Match Descriptor
        print 'Active Endpoint Response'
    elif (clusterId == 0x0006):
	pprint.pprint(data)
        # Match Descriptor Request; this is the point where I finally
        # respond to the switch.  Several messages are sent to cause the 
        # switch to join with the controller at a network level and to cause
        # it to regard this controller as valid.
        #
        # First the Active Endpoint Request
        payload1 = '\x00\x00'
        zb.send('tx_explicit',
            dest_addr_long = switchLongAddr,
            dest_addr = switchShortAddr,
            src_endpoint = '\x00',
            dest_endpoint = '\x00',
            cluster = '\x00\x05',
            profile = '\x00\x00',
            data = payload1
        )
        print 'sent Active Endpoint'
        # Now the Match Descriptor Response
        payload2 = '\x00\x00\x00\x00\x01\x02'
        zb.send('tx_explicit',
            dest_addr_long = switchLongAddr,
            dest_addr = switchShortAddr,
            src_endpoint = '\x00',
            dest_endpoint = '\x00',
            cluster = '\x80\x06',
            profile = '\x00\x00',
            data = payload2
        )
        print 'Sent Match Descriptor'
        # Now there are two messages directed at the hardware
        # code (rather than the network code.  The switch has to 
        # receive both of these to stay joined.
        payload3 = '\x11\x01\x01'
        zb.send('tx_explicit',
            dest_addr_long = switchLongAddr,
            dest_addr = switchShortAddr,
            src_endpoint = '\x00',
            dest_endpoint = '\x02',
            cluster = '\x00\xf6',
            profile = '\xc2\x16',
            data = payload2
        )
        payload4 = '\x19\x01\xfa\x00\x01'
        zb.send('tx_explicit',
            dest_addr_long = switchLongAddr,
            dest_addr = switchShortAddr,
            src_endpoint = '\x00',
            dest_endpoint = '\x02',
            cluster = '\x00\xf0',
            profile = '\xc2\x16',
            data = payload4
        )
        print 'Sent hardware join messages'

    elif (clusterId == 0xef):
        clusterCmd = ord(data['rf_data'][2])
        if (clusterCmd == 0x81):
#            print 'Instantaneous Power',
#            print ord(data['rf_data'][3]) + (ord(data['rf_data'][4]) * 256)
	    info = dict(node_id = id, type = 'Instaneous power',
		value = (ord(data['rf_data'][3]) + 
		ord(data['rf_data'][4]) * 256),
		time=time.time())
	    endpoint_data.insert(info)
        elif (clusterCmd == 0x82):
 #           print "Minute Stats:",
 #           print 'Usage, ',
            usage = (ord(data['rf_data'][3]) +
                (ord(data['rf_data'][4]) * 256) +
                (ord(data['rf_data'][5]) * 256 * 256) +
                (ord(data['rf_data'][6]) * 256 * 256 * 256) )
 #           print usage, 'Watt Seconds ',
 #           print 'Up Time,',
            upTime = (ord(data['rf_data'][7]) +
                (ord(data['rf_data'][8]) * 256) +
                (ord(data['rf_data'][9]) * 256 * 256) +
                (ord(data['rf_data'][10]) * 256 * 256 * 256))
 #           print upTime, 'Seconds'
	    info = dict(node_id = id, type = '5 minute stats',
		value = (ord(data['rf_data'][3]) + (ord(data['rf_data'][4]) * 256) +
               	(ord(data['rf_data'][5]) * 256 * 256) +
                (ord(data['rf_data'][6]) * 256 * 256 * 256) ),
		time = time.time())
	    endpoint_data.insert(info)
	    info = dict(node_id = id, type = 'uptime',
		value = (ord(data['rf_data'][7]) +
                (ord(data['rf_data'][8]) * 256) +
                (ord(data['rf_data'][9]) * 256 * 256) +
                (ord(data['rf_data'][10]) * 256 * 256 * 256) ),
		time = time.time())
	    endpoint_data.insert(info)

    elif (clusterId == 0xf0):
        clusterCmd = ord(data['rf_data'][2])
 #       print "Cluster Cmd:", hex(clusterCmd),
        if (clusterCmd == 0xfb):
 #           print "Temperature: "+ str("%.2f" % (((ord(data['rf_data'][8])*256) 
 #		+ ord(data['rf_data'][9])) /1000) )
	    info = dict(node_id = id, type = 'Temperature',
	    	value = (ord(data['rf_data'][8])*256)+ord(data['rf_data'][9]),
	    	time = time.time())
	    endpoint_data.insert(info)
 #           print "Type: "+ str(ord(data['rf_data'][3])) 
	    info = dict(id = id, type = ord(data['rf_data'][3]))
	    endpoint_table.upsert(info, ['id'])

        else:
            print "Unimplemented"
    elif (clusterId == 0xf6):
        clusterCmd = ord(data['rf_data'][2])
        if (clusterCmd == 0xfd):
 #           print "RSSI value:", ord(data['rf_data'][3])
	    info = dict(node_id = id, type = 'RSSI',
	    	value = ord(data['rf_data'][3]), time = time.time())
	    endpoint_data.insert(info)
        elif (clusterCmd == 0xfe):
 #           print "Version Information"
	    info = dict(id = id,
	    	version = binascii.hexlify(data['rf_data']))
	    endpoint_table.upsert(info,['id'])
        else:
            print data['rf_data']
    elif (clusterId == 0xf7):
	print "Motion detected:",
        clusterCmd = ord(data['rf_data'][2])
	val = 0
        if (clusterCmd == 0xfd):
	  print "on"
	  val = 1
	elif (clusterCmd == 0xfe):
	  print "off"
        info = dict(node_id = id, type = 'Motion',
	    	value = val,
	    	time = time.time())
        endpoint_data.insert(info)

    elif (clusterId == 0x8038):
#        clusterCmd = ord(data['rf_data'][2])
#	print "MGMT Network Update Request"
#	pprint.pprint(data)
	state = 0
    elif (clusterId == 0xee):
        clusterCmd = ord(data['rf_data'][2])
	state = 0
        if (clusterCmd == 0x80):
 #           print "Switch is:",
            if (ord(data['rf_data'][3]) & 0x01):
		state = 1
 #               print "ON"
            else:
		state = 0
 #               print "OFF"
	info = dict(id = id,state = state)
	endpoint_table.upsert(info,['id'])
    else:
        print "Unimplemented Cluster ID", hex(clusterId)
        print

def sendSwitch(whereLong, whereShort, srcEndpoint, destEndpoint, 
                clusterId, profileId, clusterCmd, databytes):
    
    payload = '\x11\x00' + clusterCmd + databytes
    # print 'payload',
    # for c in payload:
        # print hex(ord(c)),
    # print
    # print 'long address:',
    # for c in whereLong:
        # print hex(ord(c)),
    # print
        
    zb.send('tx_explicit',
        dest_addr_long = whereLong,
        dest_addr = whereShort,
        src_endpoint = srcEndpoint,
        dest_endpoint = destEndpoint,
        cluster = clusterId,
        profile = profileId,
        data = payload
        )

class Hub():
    @cherrypy.expose
    def index(self):
        return "Hello world!"

    @cherrypy.expose
    def status(self):
	s = HEADER + "<body>"
	s += '<div class="container">'
	s += '		<div class="sixteen columns">'
	s += '			<h1 class="remove-bottom" style="margin-top: 40px">Sensors</h1>'
	s += '			<h5>Version 0.1</h5>'
	s += '			<hr />'
	s += '		</div>'
	for node in getAllNodes():
	   s += '<div class="one-third column">'
	   if 'name' in node:
		s += '<h3>'+node['name']+'</h3>'
           s += '<ul class="square"><li><a href=node?id='+str(node['id'])+">"
	   s += node['source_addr_long'] + ":"
	   s += node['source_addr']+"</a></li>"
	   checkIn = getLatestCheckIn(node['id'])
	   s += '<li>Last check-in: ' + datetime.datetime.fromtimestamp(checkIn).strftime('%Y-%m-%d %H:%M:%S')+'</li>'
	   if 'type' in node:
		s += '<li>Type: ' + str(node['type']) + '</li></ul>'
#		s += '<li>Type: ' + nodeTypes[node['type']] + '</li></ul>'
	   s += '</div>'
	s += "</body>" + FOOTER
	return s

    @cherrypy.expose
    def node(self,id):
	node = getNodeByID(id)
	s = HEADER + "<body>"
	for type in node['types']:
	   s += "<img src=graph?id="
	   s += str(node['id'])+"&type=" +urllib.quote(type['type'])
	   s += "><br>"
	s += "</body>" + FOOTER
	return s

    @cherrypy.expose
    def graph(self,id,type):
	axes = getAxes(id,type)
	datenums=mpl.dates.date2num(axes['x'])
	plt.subplots_adjust(bottom=0.2)
	plt.xticks( rotation=25 )
	ax=plt.gca()
	xfmt = mpl.dates.DateFormatter('%Y-%m-%d %H:%M:%S')
	ax.xaxis.set_major_formatter(xfmt)
	plt.plot(datenums,axes['y'])
	output = cStringIO.StringIO()
	plt.savefig(output, format='png')
	output.seek(0)
	return cherrypy.lib.static.serve_fileobj(output,
		content_type="png", name="graph.png")

    def update(self):
        return "update node page"


def start():
    global zb
    global ser
    global db
    ser = serial.Serial(XBEEPORT, XBEEBAUD_RATE)
#    zb = XBee(ser)
#    zb.at(command="NR",paramater="\x01")
#    reply = zb.wait_read_frame()
#    while reply['id'] != "status" and reply['status'] != "\x06":
#       messageReceived(reply)
#       zb.at(command="NR",parameter="\x01")
#       reply = zb.wait_read_frame()

    zb = ZigBee(ser, callback=messageReceived)
    checkStateAll()
    print "started at ", time.strftime("%A, %B, %d at %H:%M:%S")

#        self.threads = thread.start_new_thread()

def stop():
    global zb
    global ser
    global db
    zb.halt()
    ser.close()
    db.commit()
    print "stopped at ", time.strftime("%A, %B, %d at %H:%M:%S")

#        self.bus.log("Stopping my feature.")
#        for t in self.threads:
#            thread.stop_thread(t)
#            t.join()
    
#------------------If you want to schedule something to happen -----
#scheditem = Scheduler()
#scheditem.start()

#scheditem.add_interval_job(something, seconds=sometime)

#-----------------------------------------------------------------

global endpoint_table
global endpoint_data
global endpoint_state
global meta_table
global db
db = dataset.connect('sqlite:///'+DATABASE)
# endpoints (id, uuid, source_addr_long, source_addr, name, type)
endpoint_table = db['endpoints']
pprint.pformat(endpoint_table.all)
# checkin_data (id, node_id, type, value, time) 
endpoint_data = db['checkin_data']
# state (id, node_id, state)
endpoint_state = db['state']
# schedule (id, node_id, task, cron)
schedule_data = db['schedule']
meta_table = db['metadata']

f = open(HEADER_FILE, 'r')
HEADER = f.read()
f = open(FOOTER_FILE, 'r')
FOOTER = f.read()

path   = os.path.abspath(os.path.dirname(__file__))
config= {
    'global' : {
	'server.socket_host' :  '0.0.0.0',
        'server.socket_port': 8080,
        'engine.autoreload.on': False,
        },
    '/html' : {
        'tools.staticdir.on'            : True,
        'tools.staticdir.dir'           : os.path.join(path, 'html'),
#        'tools.staticdir.content_types' : {'html': 'application/octet-stream'}
        }
}
# Subscribe to the 'main' channel in cherrypy with my timer
# tuck so the timers I use get updated
#       cherrypy.engine.subscribe("main", checkTimer.tick)
# Now just hang on the HTTP server looking for something to
# come in. The cherrypy dispatcher will update the things that
# are subscribed which will update the timers so the light
# status gets recorded.
cherrypy.engine.subscribe('start', start)
cherrypy.engine.subscribe('stop', stop)
cherrypy.quickstart(Hub(), config=config)

#print "Enter a number from 0 through 8 to send a command"
#while True:
#    try:
#        time.sleep(0.001)
#        str1 = raw_input("")
#       else:
#           print 'Unknown Command'
#    except IndexError:
#        print "empty line"
#    except KeyboardInterrupt:
#        print "Keyboard interrupt"
#        break
#    except NameError as e:
#        print "NameError:",
#        print e.message.split("'")[1]
#    except:
#        print "Unexpected error:", sys.exc_info()[0]
#        break

#print "After the while loop"
# halt() must be called before closing the serial
# port in order to ensure proper thread shutdown


