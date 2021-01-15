import appdaemon.plugins.hass.hassapi as hass
import time
import random

class smartzone(hass.Hass):
   """SMART ZONE CONTROL"""
   
   #  Example configuration
   #
   #  guestroomsmartzone:
   #     module: smartzone
   #     class: smartzone
   #     entities:
   #        climatedevice: climate.daikin_ac
   #        zoneswitch: switch.daikin_ac_guest
   #        localtempsensor: sensor.temperature_18
   #        manualoverride: input_boolean.guestairconzone
   #     coolingoffset:
   #        upperbound: 1.5
   #        lowerbound: 0.5
   #     heatingoffset:
   #        upperbound: 0.5
   #        lowerbound: 0.5
   #     conditions:
   #        - entity: binary_sensor.spare_bedroom_window
   #          targetstate: "off"
   #        - entity: input_boolean.guest_mode
   #          targetstate: "on"

   def initialize(self): 
      try: 
         self.entities = self.args["entities"]
         self.targetempsensor = self.entities["climatedevice"]
         self.aczoneswitch = self.entities["zoneswitch"]
         self.localtempsensor = self.entities["localtempsensor"]
      except Exception as ex:
         self.log(ex)
            
      if "coolingoffset" in self.args:
         self.coolingupperbounds = self.args["coolingoffset"]["upperbound"]
         self.coolinglowerbounds = self.args["coolingoffset"]["lowerbound"]
      else:       
         self.coolingupperbounds = 1.0
         self.coolinglowerbounds = 1.0
         self.log("Using default cooling settings")

      if "heatingoffset" in self.args:
         self.heatingupperbounds = self.args["heatingoffset"]["upperbound"]
         self.heatinglowerbounds = self.args["heatingoffset"]["lowerbound"]
      else:
         self.heatingupperbounds = 1.0
         self.heatinglowerbounds = 1.0
         self.log("Using default heating settings")

      if "conditions" in self.args:
         self.conditions = self.args["conditions"]
         for items in self.conditions:
            self.listen_state(self.conditionchange, items["entity"])
      else:
         self.conditions = []

      if "manualoverride" in self.entities:
         self.overridezone = self.entities["manualoverride"]
         self.hasoverride = True
      else:
         self.hasoverride = False
         
      self.randomdelay = random.randrange(0,3)
      self.listen_state(self.inroomtempchange, self.targetempsensor, attribute="temperature")
      self.listen_state(self.statechange, self.localtempsensor)

   def conditionchange(self, entity, attribute, old, new, kwargs):
      self.log("The conditional entity state has changed, updating zone accordingly.")
      self.doaction()

   def inroomtempchange(self, entity, attribute, old, new, kwargs):
      self.log("Local temp change reported by: " + entity + ", from " + str(old) + " to " + str(new) + ".")
      self.doaction()

   def statechange(self, entity, attribute, old, new, kwargs):
      self.log("Climate temp change reported: " + entity + ", from " + str(old) + " to " + str(new) + ".")
      self.doaction()

   def doaction(self):    
      
      if self.hasoverride and self.get_state(self.overridezone) == "on":
         self.log("Automatic updates are disabled.")
         return

      time.sleep(self.randomdelay)   

      # Current temp is grabbed from a local temperature sensor. It can either be a single sensor, or a sensor like min/max
      currenttemp = float(self.get_state(self.localtempsensor))
      
      # Target temp is grabbed from a climate device.
      targettemp = float(self.get_state(self.targetempsensor, attribute="temperature"))

      # Gets the current temperature from the climate device sensor
      climatetemp = float(self.get_state(self.targetempsensor, attribute="current_temperature"))
      currentswitchstate = self.get_state(self.aczoneswitch)    
      getmode = self.get_state(self.targetempsensor)
      
      if getmode == 'off' or getmode == 'heat_cool':
         # Given the aircon is off, or in auto mode this is an attempt to guess the mode of the aircon. 
         # This will allow the zones to be ready for the aircon to be switch on. This will be re-calculated 
         # when/if the setpoint changes.
         if (climatetemp > targettemp):
            mode = "cool"
         else:
            mode = "heat"
      else:
         mode = getmode
      
      if mode == "cool" or mode == "fan_only" or mode == "dry":
         lowerrange = targettemp - self.coolinglowerbounds
         upperrange = targettemp + self.coolingupperbounds
      else:
         lowerrange = targettemp - self.heatinglowerbounds
         upperrange = targettemp + self.heatingupperbounds 

      if self.IsConditionMet():
         if mode == "cool":
            if (currenttemp < lowerrange) and currentswitchstate == "on":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're below target, so switching zone off.")
               self.switchoff()
            elif (currenttemp > upperrange) and currentswitchstate == "off":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're above target, switching zone on")
               self.switchon()
         elif mode == "heat":
            if (currenttemp >= upperrange) and currentswitchstate == "on":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're getting a bit warm so switch zone off")
               self.switchoff()
            elif (currenttemp < lowerrange) and currentswitchstate == "off"):
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". It's getting cool, turning zone back on")
               self.switchon()
         elif mode == "fan_only" or mode == "dry":
            self.log("Fan or dry mode, so open the zone")
            self.switchon()
      else:
         self.switchoff()
      
   def switchon(self):
      self.call_service("switch/turn_on", entity_id = self.aczoneswitch)
      time.sleep(self.randomdelay)
      if self.get_state(self.aczoneswitch) == "off":
         self.switchon()
      
   def switchoff(self):
      self.call_service("switch/turn_off", entity_id = self.aczoneswitch)
      time.sleep(self.randomdelay)
      if self.get_state(self.aczoneswitch) == "on":
         self.switchoff()

   def IsConditionMet(self):
   # Iterate through the conditions and check if they are all true. If not, conditions are not met
      NumberOfConditions = len(self.conditions)
      if NumberOfConditions == 0:
         return True
      try:
         for item in self.conditions:
            entity = item["entity"]
            targetstate = item["targetstate"]            
            state = self.get_state(entity)
            if str(state.lower()) != str(targetstate.lower()):
               self.log(entity + " should be " + targetstate + " but it's not, it's " + state)
               return False
      except Exception as dex:
         self.log("Condition loop error: " + dex)
         return True
      return True
