# ooler-mqtt-bridge
A bridge between an [Ooler](https://chilisleep.co.uk/products/ooler-sleep-system)
bed cooling/heating system and MQTT, targetting Home Assistant

## Overview
This repo contains a service to allow for integrating your Ooler device with
Home Assistant, using Bluetooth LE to talk to the Ooler, and MQTT to
communicate with Home Assistant. As such, you will need an MQTT broker set up
somewhere, and hardware capable of speaking Bluetooth LE on the system you are
running this on. I'm using a Raspberry Pi Zero W.

The data that are exposed are:
 * Desired temperature (°C)
 * Actual temperature (°C)
 * Power state ("off" or "auto", "auto" being on)
 * Fan speed ("Silent", "Regular", or "Boost")
 * Water level (which I think is percentage, but have only seen values of 100 and 50 so far)
 * UV cleaning state

Parameters that can be controlled are:
 * Desired temperature (°C)
 * Power state
 * Fan speed
 * UV cleaning

Whilst this does target Home Assistant, and publishes an autoconfiguration
message for Home Assistant to pick up on to seamlessly integrate it as an HVAC
unit, there is nothing stopping you from using it without Home Assistant, as
long as you are capable of parsing JSON in your consumer. Take a look at the
configuration message sent by the bridge to see where to find the data.

This repo contains two key parts:
 * A module for talking to Ooler devices
 * A script which uses this module to send status reports via MQTT, and to
   receive control commands

If anyone cares I would be happy to split out the module into its own thing;
for simplicity/not having to look up how to create a PyPI package I've left it
in here for now.

## Installation/Configuration
Installation consists of pulling in the packages listed in requirements.txt and
putting the files of this repo somewhere. Optionally customise and install the
systemd unit file provided to have it be nicely managed.

To configure it, edit the yaml file that is provided and pass this as an option
on the command line. The configuration is documented in this file.

## Limitations
I had intended to make this support either staying connected indefinitely or
disconnecting/reconnecting to read/set state, but I had difficulty with fully
disconnecting, so it only supports permanent connection. Since Bluetooth LE 
only allows a single connection at a time, this means you cannot use the app
to control the Ooler whilst this is running.

I have had issues with Python segfaulting, so I'm not able to properly handle
all errors, and so I'm running this with it set to restart when it falls over.
I would advise running it like this, e.g. with systemd.

This only works with unencrypted MQTT brokers - I imagine support shouldn't be
too hard to add, it's just not something I need at the moment.

The Ooler works in Fahrenheit internally, so the Celsius mappings are a bit
clunky (and greater than the amount of precision allowed by the device). This
is also true of the app. The underlying library allows for control via
Fahrenheit, but the bridge only supports Celsius.

I have only been able to test this on one device, so I don't know if there are
any differences between different setups. This also only supports one device
being configured, again, because I only have the one so wouldn't be able to use
or test supporting more than one.
