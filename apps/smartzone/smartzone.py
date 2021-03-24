import appdaemon.plugins.hass.hassapi as hass
import time
import random
import json

class smartzone(hass.Hass):
   """SMART ZONE CONTROL"""   
   def initialize(self):          
      try: 
         self.entities = self.args["entities"]
         self.targetempsensor = self.entities["climatedevice"]
         self.aczoneswitch = self.entities["zoneswitch"]
         self.localtempsensor = self.entities["localtempsensor"]
         self.exteriortempsensor = self.entities["exteriortempsensor"]
      except Exception as ex:
         self.log(ex)

      if "coolingoffset" in self.args:
         self.coolingupperbounds = self.args["coolingoffset"]["upperbound"]
         self.coolinglowerbounds = self.args["coolingoffset"]["lowerbound"]
         self.log("Got cooling settings from updated configuration: " + str(self.coolingupperbounds) + " over and " + str(self.coolinglowerbounds) + " under")
      else:       
         self.coolingupperbounds = 1.0
         self.coolinglowerbounds = 1.0
         self.log("Using default cooling settings")

      if "heatingoffset" in self.args:
         self.heatingupperbounds = self.args["heatingoffset"]["upperbound"]
         self.heatinglowerbounds = self.args["heatingoffset"]["lowerbound"]
         self.log("Got heating settings from updated configuration: " + str(self.heatingupperbounds) + " over and " + str(self.heatingupperbounds) + " under")
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

      # setup various 
      self.listen_state(self.inroomtempchange, self.targetempsensor, attribute="temperature")
      self.listen_state(self.statechange, self.localtempsensor)
      self.listen_state(self.climatedevicechange, self.targetempsensor)

   def climatedevicechange(self, entity, attribute, old, new, kwargs):
      self.log("New: " + str(new))
      self.log("Old: " + str(old))
      if old == "off" and new != "off" and self.IsConditionMet():
         self.log("The climate device state has changed, updating zones accordingly.")
         time.sleep(self.randomdelay)  
         self.switchon()
      elif new == "off":
         self.log("Climate State = " + new)
         time.sleep(self.randomdelay)  
         self.switchoff()
      
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
      
      if getmode == 'off' or getmode == 'heat_cool' or getmode == 'auto':
         # Given the aircon is off, or in auto mode this is an attempt to guess the mode of the aircon. 
         # This will allow the zones to be ready for the aircon to be switch on. This will be re-calculated 
         # when/if the setpoint changes.
         if climatetemp >= targettemp or float(self.get_state(self.exteriortempsensor)) >= targettemp:
            mode = "cool"
         else:
            mode = "heat"
      else:
         mode = getmode
      self.log("Climate Mode: " + mode + ". Target temp is: " + str(targettemp) + ", Climate reported temp is: " + str(climatetemp))
      
      if mode == "cool" or mode == "fan_only" or mode == "dry":
         lowerrange = targettemp - self.coolinglowerbounds
         upperrange = targettemp + self.coolingupperbounds
      else:
         lowerrange = targettemp - self.heatinglowerbounds
         upperrange = targettemp + self.heatingupperbounds 
      # lowerrange is the temperature set by the climate device, minus the lower bound
      # For example, if lower bound is 0.5 and the target temp of the climate device is 23, the lower bound will be 22.5.
      
      # upperrange is the temperature set by the climate device, plus the upper bound
      # For example, if upper bound is 1 and the target temp of the climate device is 23, the lower bound will be 24.
      
      # this will give you the temperature range that the zone should be open for
      # in this case, if the currenttemp range is between 22.5 and 24 the zone will open. If not, the zone will close.
      
      

      if self.IsConditionMet():
         if mode == "cool":
            if (currenttemp < lowerrange) and currentswitchstate == "on":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're at or below lower target, so switching zone off.")
               self.switchoff()
            elif (currenttemp < lowerrange) and currentswitchstate == "off":
               self.log(str(currenttemp) + " is below the target range of " + str(lowerrange) + " to " + str(upperrange) + " but zone is already off.")
            elif (currenttemp > upperrange) and currentswitchstate == "off":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're at or above upper target, switching zone on")
               self.switchon()
            elif (currenttemp > upperrange) and currentswitchstate == "on":
               self.log(str(currenttemp) + " is above the target range of " + str(lowerrange) + " to " + str(upperrange) + " but zone is already on.")
            else:
               self.log(str(currenttemp) + " is in the the target range of " + str(lowerrange) + " to " + str(upperrange))
         elif mode == "heat":
            if (currenttemp >= upperrange) and currentswitchstate == "on":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're getting a bit warm so switching zone off")
               self.switchoff()
            elif (currenttemp >= upperrange) and currentswitchstate == "off":
               self.log(str(currenttemp) + " is above the target range of " + str(lowerrange) + " to " + str(upperrange) + " but zone is already off.")               
            elif (currenttemp < lowerrange) and currentswitchstate == "off":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're getting cool, so switching zone on")
               self.switchon()
            elif (currenttemp < lowerrange) and currentswitchstate == "on":
               self.log(str(currenttemp) + " is below the target range of " + str(lowerrange) + " to " + str(upperrange) + " but zone is already on.")          
            else:
               self.log(str(currenttemp) + " is in the the target range of " + str(lowerrange) + " to " + str(upperrange))
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
               self.log(entity + " needs to be in " + targetstate + " state but it's not, so we'll ignore the temperature change")
               return False
      except Exception as dex:
         self.log("Condition loop error: " + dex)
         return True
      return True
