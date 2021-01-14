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

| Name               |   Type    | Default      | Description                                                             |
| ------------------ | :-------: | ------------ | ----------------------------------------------------------------------- |
| `climatedevice`    | `string`  | **Required** | An entity_id within the `climate` domain.                               |
| `zoneswitch`       | `string`  | **Required** | An entity_id within the `switch` domain.                                |
| `localtempsensor`  | `string`  | Optional     | An entity_id within the `camera` domain, for streaming live vacuum map. |
| `manualoverride`   | `string`  | Optional     | Entity_id of an input_boolean                                           |
| `coolingoffset`    | `string`  | `default`    | Path to image of your vacuum cleaner. Better to have `png` or `svg`.    |
| `heatingoffset`    | `boolean` | `true`       | Show friendly name of the vacuum.                                       |
| `conditions`       | `boolean` | `false`      | Compact view without image.                                             |
| `stats`            | `object`  | Optional     | Custom per state stats for your vacuum cleaner                          |
| `actions`          | `object`  | Optional     | Custom actions for your vacuum cleaner.                                 |


| Name           |   Type    | Default      | Description                                                             |
| -------------- | :-------: | ------------ | ----------------------------------------------------------------------- |
| `upperbound`| `float`  | Optional | An entity_id within the `climate` domain.                               |
| `lowerbound`   | `float`  | optional | An entity_id within the `switch` domain.                                |

| Name           |   Type    | Default      | Description                                                             |
| -------------- | :-------: | ------------ | ----------------------------------------------------------------------- |
| `entity`| `string`  | Optional | An entity_id within the `climate` domain.                               |
| `targetstate`   | `string`  | optional | An entity_id within the `switch` domain.                                |

