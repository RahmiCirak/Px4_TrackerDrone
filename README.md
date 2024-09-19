# Px4_TrackerDrone
Vision based, UAV tracker UAV

This project was developed for educational purposes. I based my work on Ark Electronics' "ROS2_PX4_Offboard_Example" and made some modifications to it. Initially, I created two launch files and run UAV models named gz_500 and gz_500_depth.

As I am a beginner, my initial approach was quite basic. I also linked a depth camera with YOLOv8 to implement object tracking, though this part of the project is still in its early stages and requires further refinement.

I intend to continue improving this repository as I develop my skills.

----------------------------------------------------------------------

First of all I use ARK Electronics's offboard example :https://github.com/ARK-Electronics/ROS2_PX4_Offboard_Example
this is offer a sigle UAV's control and I add second drone (all the control are sama I just chance the topic's names and target_sys parameter.) and Tracking algorithm with camera image.

----------------------------------------------------------------------
For the setup you should check the link and try to run single drone and after you can launch second drone which is here 
after all you can run "uav_camera-det.py" and the setup is done .
