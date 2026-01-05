from time import sleep
from datetime import datetime
from statemachine import StateMachine, State
import board
import adafruit_ahtx0
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import serial
from gpiozero import Button, PWMLED
from threading import Thread
from math import floor

## DEBUG flag - boolean value to indicate whether or not to print status messages on the console of the program
DEBUG = True

## Creates an I2C instance to communicate with devices on the I2C bus
i2c = board.I2C()

## Initialize Temperature sensor
thSensor = adafruit_ahtx0.AHTx0(i2c)

## Initialize the serial connection
ser = serial.Serial(
        port='/dev/ttyS0',
        baudrate = 115200,              # This sets the speed of the serial interface in bits/second
        parity=serial.PARITY_NONE,      # Disable parity
        stopbits=serial.STOPBITS_ONE,   # Serial protocol will use one stop bit
        bytesize=serial.EIGHTBITS,      # We are using 8-bit bytes 
        timeout=1                       # Configure a 1-second timeout
)

## Two LEDs, utilizing GPIO 18, and GPIO 23
redLight = PWMLED(18)
blueLight = PWMLED(23)

## Class intended to manage the 16x2 Display
class ManagedDisplay():
    
    def __init__(self):

        ## Setup the six GPIO lines to communicate with the display
        self.lcd_rs = digitalio.DigitalInOut(board.D17)
        self.lcd_en = digitalio.DigitalInOut(board.D27)
        self.lcd_d4 = digitalio.DigitalInOut(board.D5)
        self.lcd_d5 = digitalio.DigitalInOut(board.D6)
        self.lcd_d6 = digitalio.DigitalInOut(board.D13)
        self.lcd_d7 = digitalio.DigitalInOut(board.D26)

        # Modify this if you have a different sized character LCD
        self.lcd_columns = 16
        self.lcd_rows = 2 

        # Initialise the lcd class
        self.lcd = characterlcd.Character_LCD_Mono(self.lcd_rs, self.lcd_en, 
                    self.lcd_d4, self.lcd_d5, self.lcd_d6, self.lcd_d7, 
                    self.lcd_columns, self.lcd_rows)

        # wipe LCD screen before we start
        self.lcd.clear()

    ## Method used to cleanup the digitalIO lines that are used to run the display
    def cleanupDisplay(self):

        # Clear the LCD first - otherwise we won't be abe to update it
        self.lcd.clear()
        self.lcd_rs.deinit()
        self.lcd_en.deinit()
        self.lcd_d4.deinit()
        self.lcd_d5.deinit()
        self.lcd_d6.deinit()
        self.lcd_d7.deinit()
        
    ## Convenience method to clear the display
    def clear(self):
        self.lcd.clear()

    ##Convenience method to update the message
    def updateScreen(self, message):
        self.lcd.clear()
        self.lcd.message = message

## Initialize display
screen = ManagedDisplay()

## Manages the three states handled by the thermostat: off, heat, cool
class TemperatureMachine(StateMachine):

    off = State(initial = True)
    heat = State()
    cool = State()

    ## Default temperature setPoint is 72 degrees Fahrenheit
    setPoint = 72

    ## cycle - event that transitions between the three states
    cycle = (
        off.to(heat) |
        heat.to(cool) |
        cool.to(off)
    )

    ## Action performed when the state machine transitions into the 'heat' state
    def on_enter_heat(self):
        
        self.updateLights()

        if(DEBUG):
            print("* Changing state to heat")

    ## Action performed when the statemachine transitions out of the 'heat' state
    def on_exit_heat(self):
        
        redLight.off()

    ## Action performed when the state machine transitions into the 'cool' state
    def on_enter_cool(self):
        
        self.updateLights()

        if(DEBUG):
            print("* Changing state to cool")
    
    ## Action performed when the statemachine transitions out of the 'cool' state
    def on_exit_cool(self):
        
        blueLight.off()

    ## Action performed when the state machine transitions into the 'off' state
    def on_enter_off(self):
        
        redLight.off()
        blueLight.off()

        if(DEBUG):
            print("* Changing state to off")
    
    ## Utility method used to send events to the state machine
    ## Triggered by the button_pressed event handler for the first button
    def processTempStateButton(self):
        if(DEBUG):
            print("Cycling Temperature State")

        self.cycle()

    ## Utility method used to update the setPoint for the temperature by a single degree
    ## This is triggered by the button_pressed event handler for the second button
    def processTempIncButton(self):
        if(DEBUG):
            print("Increasing Set Point")

        self.setPoint += 1
        self.updateLights()

    ## Utility method used to update the setPoint for the temperature by a single degree
    ## This is triggered by the button_pressed event handler for the third button
    def processTempDecButton(self):
        if(DEBUG):
            print("Decreasing Set Point")

        self.setPoint -= 1
        self.updateLights()

    ## Utility method to update the LED indicators on the Thermostat
    def updateLights(self):
        ## Make sure we are comparing temperatires in the correct scale
        temp = floor(self.getFahrenheit())
        redLight.off()
        blueLight.off()
    
        ## Verify values for debug purposes
        if(DEBUG):
            print(f"State: {self.current_state.id}")
            print(f"SetPoint: {self.setPoint}")
            print(f"Temp: {temp}")

        # Determine visual identifiers

        if self.current_state.id == "off":
            redLight.off()
            blueLight.off()

        elif self.current_state.id == "heat":
            blueLight.off()
            if temp < self.setPoint:
                redLight.pulse()     # fade when below setpoint
            else:
                redLight.on()        # solid when at/above setpoint

        elif self.current_state.id == "cool":
            redLight.off()
            if temp > self.setPoint:
                blueLight.pulse()    # fade when above setpoint
            else:
                blueLight.on()       # solid when at/below setpoint


    ## kicks off the display management functionality of the thermostat
    def run(self):
        myThread = Thread(target=self.manageMyDisplay)
        myThread.start()

    ## Get the temperature in Fahrenheit
    def getFahrenheit(self):
        t = thSensor.temperature
        return (((9/5) * t) + 32)
    
    ##  Configure output string for the Thermostat Server
    def setupSerialOutput(self):
        
        state = self.current_state.id
        temp_f = floor(self.getFahrenheit())
        output = f"{state},{temp_f},{self.setPoint}"
        return output
    
    ## Continue display output
    endDisplay = False

    ##  This function is designed to manage the LCD Display
    def manageMyDisplay(self):
        counter = 1
        altCounter = 1
        while not self.endDisplay:

            if(DEBUG):
                print("Processing Display Info...")
    
            ## Grab the current time        
            current_time = datetime.now()
    
            ## Setup display line 1
            lcd_line_1 = current_time.strftime("%m/%d/%Y %H:%M") + "\n"
    
            ## Setup Display Line 2
            if(altCounter < 6):
                
                lcd_line_2 = f"Temp: {floor(self.getFahrenheit())}F"
    
                altCounter = altCounter + 1
            else:
                
                lcd_line_2 = f"{self.current_state.id.upper()} SP:{self.setPoint}F"
    
                altCounter = altCounter + 1
                if(altCounter >= 11):

                    # Run the routine to update the lights every 10 seconds
                    self.updateLights()
                    altCounter = 1
    
            ## Update Display
            screen.updateScreen(lcd_line_1 + lcd_line_2)
    
            ## Update server every 30 seconds
            if(DEBUG):
               print(f"Counter: {counter}")
            if((counter % 30) == 0):
                
                ser.write((self.setupSerialOutput() + "\n").encode())

                counter = 1
            else:
                counter = counter + 1
            sleep(1)

        ## Cleanup display
        screen.cleanupDisplay()


## Setup the State Machine
tsm = TemperatureMachine()
tsm.run()

## Configure the green button to use GPIO 24 and to execute the method to cycle the thermostat when pressed
greenButton = Button(24)

greenButton.when_pressed = tsm.processTempStateButton

## Configure the Red button to use GPIO 25 and to execute the function to increase the setpoint by a degree
redButton = Button(25)

redButton.when_pressed = tsm.processTempIncButton

## Configure the Blue button to use GPIO 12 and to execute the function to decrease the setpoint by a degree
blueButton = Button(12)

blueButton.when_pressed = tsm.processTempDecButton

## Setup loop variable
repeat = True

## Repeat until the user creates a keyboard interrupt (CTRL-C)
while repeat:
    try:

        sleep(30)

    except KeyboardInterrupt:

        ## Catch the keyboard interrupt (CTRL-C) and exit cleanly
        print("Cleaning up. Exiting...")

        ## Stop the loop
        repeat = False
        
        ## Close down the display
        tsm.endDisplay = True
        sleep(1)