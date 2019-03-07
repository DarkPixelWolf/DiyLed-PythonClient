import threading
import time

light_name = "Light"
num_leds = 60
state = True
brightness = 100
mode = "Color"
modes = ["Color", "Rainbow"]
rgb = [255, 50, 255]

def loopClient(diyledclient):
	while True:
		diyledclient.loop()
		time.sleep(1)
		
def valueCallback(prop, value):
	global state
	global brightness
	global rgb
	global mode
	
	# do your processing/handling in here
	if (prop == "power"):
		stateString = value # type string
		if (stateString == "toggle"):
			state = not state
		elif (stateString == "true"):
			state = True
		elif (stateString == "false"):
			state = False
		print("Power property changed to: " + str(state))
	elif (prop == "brightness"):
		brightness = value # type int
		print("Brightness property changed to: " + str(brightness))
	elif (prop == "color"):
		rgb = value # type int array[3]
		print("Color property changed to: [" + str(rgb[0]) + ", " + str(rgb[1]) + ", " + str(rgb[2]) + "]")
	elif (prop == "mode"):
		mode = value # type string
		print("Mode property changed to: " + str(mode))
		
def stateGetCallback():
	return DeviceProperties(light_name, num_leds, state, brightness, mode, modes, rgb[0], rgb[1], rgb[2])

if __name__ == "__main__":
	client = DiyLedClient(valueCallback, stateGetCallback)
	client.begin()
	
	clientLoop = threading.Thread(target = loopClient, args = (client,))
	clientLoop.daemon = True
	clientLoop.start()
