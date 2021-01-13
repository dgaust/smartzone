import appdaemon.plugins.hass.hassapi as hass
import time
import random

class smartzone(hass.Hass):
   """SMART ZONE CONTROL"""
    
   def initialize(self):
      
      # Initialise the minimum entities required to control the zone.
      # Required:
      # climatedevice: The climate domain device from ha (i.e. climate.airconditioner)
      # zoneswitch: The switch domain device that controls the zone
      # localtempsensor: The sensor that reports a temperature as state
      # upperbound: The amount above the climate device setpoint the local temperature sensor should be able to achieve before the action.
      # lowerbound: The amount below the climate device setpoint the local temperature sensor should be able to achieve before the action.
      
      try: 
         self.entities = self.args["entities"]
         self.targetempsensor = self.entities["climatedevice"]
         self.aczoneswitch = self.entities["zoneswitch"]
         self.localtempsensor = self.entities["localtempsensor"]
         self.upperbounds = float(self.entities["upperbound"])
         self.lowerbounds = float(self.entities["lowerbound"])
      except Exception as ex:
         self.log(ex)
      
      # self.conditions = []
      try:
         self.conditions = self.args["conditions"]
         self.conditionentity = self.conditions["entity"]
         self.conditionstate = self.conditions["targetstate"]
         self.log("entity " + self.conditionentity + " should be " + self.conditionstate + " before zone will open.")
      except Exception as ex:
         self.log(ex)
         
      self.randomdelay = random.randrange(0,3)
      self.listen_state(self.inroomtempchange, self.targetempsensor, attribute="temperature")
      self.listen_state(self.statechange, self.localtempsensor)

   def inroomtempchange(self, entity, attribute, old, new, kwargs):
      try:
         self.log("Local temp change reported by: " + entity + ", from " + str(old) + " to " + str(new) + ".")
      except Exception as ex:
         self.log(ex)
      self.doaction()

   def statechange(self, entity, attribute, old, new, kwargs):
      try:
         self.log("Climate temp change reported: " + entity + ", from " + str(old) + " to " + str(new) + ".")
      except Exception as ex:
         self.log(ex)
      self.doaction()

   def doaction(self):
      isconditionmet = True
      try:
         self.log(self.conditionentity)
         self.log(self.conditionstate)
         state = self.get_state(self.conditionentity)
         if state == self.conditionstate:
            isconditionmet = True
         else:
            isconditionmet = False
         self.log("Has conditions and the condition is met: " + str(isconditionmet))
      except Exception as ex:
         self.log(ex)
         self.log("Has no conditions")
         
      # Current temp is grabbed from a local temperature sensor. It can either be a single sensor, or a sensor like min/max
      currenttemp = float(self.get_state(self.localtempsensor))
      # Target temp is grabbed from a climate device.
      targettemp = float(self.get_state(self.targetempsensor, attribute="temperature"))
      climatetemp = float(self.get_state(self.targetempsensor, attribute="current_temperature"))
      currentswitchstate = self.get_state(self.aczoneswitch)
      self.log("Currently zone is " + currentswitchstate)
      
      getmode = self.get_state(self.targetempsensor)
      if getmode == 'off' or getmode == 'heat_cool':
         # Attempt to guess the mode of the aircon, especially if heat_cool mode. If off, this just allows for zones to be open in preparation
         # of the aircon being switch on. Mode will change depending on the set point.
         if (climatetemp > targettemp):
            mode = "cool"
         else:
            mode = "heat"
      else:
         mode = getmode
      self.log("Mode is: " + mode)
      # lowerrange is the temperature set by the climate device, minus the lower bound
      # For example, if lower bound is 0.5 and the target temp of the climate device is 23, the lower bound will be 22.5.
      lowerrange = targettemp - self.lowerbounds
      # upperrange is the temperature set by the climate device, plus the upper bound
      # For example, if upper bound is 1 and the target temp of the climate device is 23, the lower bound will be 24.
      upperrange = targettemp + self.upperbounds  
      # this will give you the temperature range that the zone should be open for
      # in this case, if the currenttemp range is between 22.5 and 24 the zone will open. If not, the zone will close.
      
      # If switch is on, and we drop down past the lowerbound, turn it off.
      # If the switch is off, and we go over the upper bound, turn it on.
      time.sleep(self.randomdelay)
      if isconditionmet:
         if mode == "cool":
            if (currenttemp < lowerrange) and currentswitchstate == "on":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're below target, so switching zone off.")
               self.switchoff()
            elif (currenttemp > upperrange) and currentswitchstate == "off":
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're above target, switching zone on")
               self.switchon()
         elif mode == "heat":
            if (currenttemp >= upperrange):
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're getting a bit warm so switch zone on")
               self.switchoff()
            elif (currenttemp < lowerrange):
               self.log("Current temp: " + str(currenttemp) + ", Target temp is: " + str(targettemp) + ". Target range is " + str(lowerrange) + " to " + str(upperrange) + ". We're warm enough so switching zone off")
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
