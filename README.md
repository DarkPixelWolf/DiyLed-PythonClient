# DiyLed-PythonClient
This is the clientside of the DiyLed system for devices compatible with python3

[Server]()
[Client for ESP]()
[DiyLed App]()

#### What is the DiyLed system?
The DiyLed system is my version of systems/enviroments like Philips Hue (sort of). This system was created to

* allow the use of any device that is not supported by Amazon Alexa and Philips Hue
* give the user a overall higher customizability regarding control, light effects etc
* be a kind of challenge/project for myself to be honest

#### Functions
* fully customizable server and client (for python3 and esp)
* full Alexa integration
* compatible DiyLed App
* no static ip setup needed (is recommended though)

#### Installation
*I recommend using a Raspberry Pi of any revision (with LAN is better) as it supports python3, doesn't use a lot of power, is capable of controling led strips via pwm pins and was used to test the client.*

The installation is very simple, just download the `DiyLedClient.py` file and place it into your project folder.
That is it! Now you can use the library by importing it:
```python
from DiyLedClient import DiyLedClient, DeviceProperties
```

#### Usage
After importing the library you have to create some functions for the client to work:

ValueCallback, this function is called when the server wants to change a property, the types of `value` are specified below the example:
```python
def valueCallback(prop, value):
	# do your processing/handling in here
	if (prop == "power"):
		print("Power property changed to: " + str(value))
	elif (prop == "brightness"):
		print("Brightness property changed to: " + str(value))
	elif (prop == "color"):
		print("Color property changed to: [" + str(value[0]) + ", " + str(value[1]) + ", " + str(value[2]) + "]")
	elif (prop == "mode"):
		print("Mode property changed to: " + str(value))
```
`prop` Name | `value` Type | Values | Description
--- | --- | --- | ---
power | string | toggle, true, false | The state of the light, on/off
brightness | int | 0 - 255 | The brightness of the light
color | int array[3] | 3 values 0 - 255 | RGB color values as array
mode | string | defined by MODES array | Mode of the light, MODES array is provided when creating a DiyLedClient object


StateGetCallback, this function is used by the DiyLedClient to get the current state of the device, as this is completely up to you, the client uses a callback function to get the state from your script, argument types and meaning are specified below the example:
```python
def stateGetCallback():
	return DeviceProperties(light_name, num_leds, state, brightness, mode, modes, r, g, b)
```
Argument | Type | Values | Description
--- | --- | --- | ---
light_name | string | * | The name of your light
num_leds | int | * | The number of leds your light has
state | boolean | True, False | The state of your light, e.g. on=True/off=False
brightness | int | 0 - 255 | The brightness of your light
mode | string | * | The mode the light is currently in
modes | string[] | * | An array containing all available modes


*Optional:* If you don't have a looping function you have to create one for the client to work properly:
```python
import threading
import time

def loopClient(diyledclient):
	while True:
		diyledclient.loop()
		time.sleep(1)
```
The loop function doesn't need a delay of one second between execution, but this is recommended, lower might be better under certain conditions.

After creating these functions you can create a DiyLedClient object and initialize it like so:
```python
client = DiyLedClient(valueCallback, stateGetCallback)
client.begin()
```
If you want to see a log of events you can add `DEBUG=True` as an additional argument.

Great! Now there is only one thing left. Make sure the clients `loop()` function is called in a loop:
```python
client.loop()
```
*If you created the loopClient function from before:*
```python
clientLoop = threading.Thread(target = loopClient, args = (client,))
clientLoop.daemon = True
clientLoop.start()
```

That is it! The repository contains a `clientExample.py` file for reference.
