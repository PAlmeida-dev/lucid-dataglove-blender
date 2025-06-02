# lucid-dataglove-blender
Project Based on LucidVR Gloves implementation, adapted to act as a DataGlove inside blender. Rigged hands model made by 3dhaupt, published at https://free3d.com/3d-model/rigged-hands-28855.html in Dec 16, 2015.


# How to use
1. Adjust SERIAL_PORT to the current USB port used by the LucidGlove and HOST,PORT to desired values inside `glove_serial_read_socket_send.py`
2. Open Blender and load the `hand_scene` file
3. Under Blender's scripting tab, adjust HOST,PORT to the same values used during step 1 in case you've changed them
4. Execute `python ./glove_serial_read_socket_send.py` using any terminal
5. Execute the blender script

# Important
1. The `blender_socket_read.py` script is already imported at Blender scene, but you can copy/paste it there if it's missing
2. The code was designed to work using the hand_scene and it will search for the specific paths and bones placed inside of it. To use it with other files, change the mapping dictionaries inside `blender_socket_read.py` and paste them inside blender.
