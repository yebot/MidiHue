#!/usr/bin/python
from phue import Bridge
import rtmidi

# import json
import time

from constants import BRIDGE_IP_ADDRESS, STUDIO_LIGHT, DEFAULT, HUE
from schemes import SCHEME

b = Bridge(BRIDGE_IP_ADDRESS)

# If the app is not registered and the button is not pressed, press the button and call connect() (this only needs to be run a single time)
# b.connect()

# Get the bridge state (This returns the full dictionary that you can explore)
bridge_dict = b.get_api()

# with open("bridge_dict.json", "w") as json_file:
#     json.dump(bridge_dict, json_file, indent=4)

# Iterate through the groups to find the one named "Studio"
for group_id, group_info in bridge_dict["groups"].items():
    if group_info["name"] == "Studio":
        # print("Group ID for 'Studio':", group_id)
        studio_group_id = group_id

light_names = b.get_light_objects("name")

studio_lights = {
    custom_name: light_names[actual_name]
    for custom_name, actual_name in STUDIO_LIGHT.items()
    if actual_name in light_names
}


def set_studio_light(
    light_name,
    hue,
    transition_time=DEFAULT["transition_time"],
    brightness=DEFAULT["brightness"],
    saturation=DEFAULT["saturation"],
):
    light_params = {
        "transitiontime": transition_time * 10,
        "on": True,
        "bri": brightness,
    }
    if hue.lower() == "black":
        light_params["on"] = False
    elif hue.lower() == "white":
        light_params["ct"] = DEFAULT["color_temp"]
        light_params["bri"] = 150
    else:
        light_params["sat"] = saturation
        light_params["hue"] = HUE[hue.lower()]

    b.set_light(
        light_name,
        light_params,
    )


def set_all_studio_lights(
    hue,
    transition_time=DEFAULT["transition_time"],
    brightness=DEFAULT["brightness"],
    saturation=DEFAULT["saturation"],
):
    for light_name in STUDIO_LIGHT.values():
        set_studio_light(
            light_name,
            hue,
            transition_time=transition_time,
            brightness=brightness,
            saturation=saturation,
        )


midiin = rtmidi.MidiIn()


# Function to handle incoming MIDI messages
def midi_callback(message, time_stamp):
    message, deltatime = message
    print(f"{message} @ {time_stamp}")
    note, velocity = message[1], message[2]

    # Check if the note is ON and is in the SCHEME
    if message[0] == 144 and velocity > 0 and note in SCHEME:
        apply_scheme(note)


def apply_scheme(note):
    # Get the scheme for the note
    scheme = SCHEME[note]
    for light_position, color in scheme.items():
        actual_light_name = STUDIO_LIGHT[light_position]
        set_studio_light(actual_light_name, color)


# Open virtual MIDI port
midiin.open_virtual_port("HueMidi Input")

# Set the callback function
midiin.set_callback(midi_callback)

print("Listening for MIDI messages...")


# Keep the program running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")

finally:
    midiin.close_port()
    del midiin
