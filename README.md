# smartzone

An appdaemon app to automatically control climate zones (on/off) only depending on localised temperatures. Supports multiple conditions being set before action is taken (ALL conditions must be met), and manual override with an input_boolean

A typical example of the configuration in the apps.yaml file will look like

```
guestroomsmartzone:
  module: smartzone
  class: smartzone
  entities:
    climatedevice: climate.daikin_ac
    zoneswitch: switch.daikin_ac_guest
    localtempsensor: sensor.temperature_18
    manualoverride: input_boolean.guestairconzone
    coolingoffset:
      upperbound: 1.5
      lowerbound: 0.5
    heatingoffset:
      upperbound: 0.5
      lowerbound: 0.5
    conditions:
      - entity: binary_sensor.spare_bedroom_window
        targetstate: "off"
      - entity: input_boolean.guest_mode
        targetstate: "on"
```

Here is what every option means:

| Name               |   Type       | Default      | Description                                                             |
| ------------------ | :----------: | ------------ | ----------------------------------------------------------------------- |
| `climatedevice`    | `string`     | **Required** | An entity_id within the `climate` domain.                               |
| `zoneswitch`       | `string`     | **Required** | An entity_id within the `switch` domain.                                |
| `localtempsensor`  | `string`     | Optional     | An entity_id within the `camera` domain, for streaming live vacuum map. |
| `manualoverride`   | `string`     | Optional     | Entity_id of an input_boolean                                           |
| `coolingoffset`    | `object`     | Optional     | Temperature offset object. If no object provided defaults to 1.0        |
| `heatingoffset`    | `object`     | Optional     | Temperature offset object. If no object provided defaults to 1.0        |
| `conditions`       | `object`     | Optional     | Conditions object                                                       |


| ** TEMPERATURE OFFSET OBJECT **                                                                                     |
| Name           |   Type    | Default      | Description                                                             |
| -------------- | :-------: | ------------ | ----------------------------------------------------------------------- |
| `upperbound`   | `float`   | Required     | Value above setpoint that localtempsensor can reach. Required if coolingoffset or heatingoffset is specified                     |
| `lowerbound`   | `float`   | Required     | Value below setpoint that localtempsensor can reach                     |


| ** CONDITION OBJECT **                                                                                              |
| Name           |   Type    | Default      | Description                                                             |
| -------------- | :-------: | ------------ | ----------------------------------------------------------------------- |
| `entity`       | `string`  | Required     | An entity_id within the `climate` domain.                               |
| `targetstate`  | `string`  | Required     | An entity_id within the `switch` domain.                                |

