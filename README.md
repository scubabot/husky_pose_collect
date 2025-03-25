## README

### Overview

This code records position data from an OptiTrack camera system. Although it was developed for a Clearpath HUSKY A200, it is not specific to that platform and can be adapted for any system that publishes pose data in a similar format. 

### Dependencies

- ROS Noetic (with Python3)
- ROS Packages: `rospy`, `geometry_msgs`, `tf`, `matplotlib`

Make sure to install these and that your ROS workspace is properly set up.

```bash
sudo apt install ros-noetic-tf python3-matplotlib
```

### Setup

1. Create a Catkin Workspace:
    If you have not yet, create and initialize your workspace:
```bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
catkin_init_workspace
```

2. Create/Place the Package:
    - Place your package (e.g., `husky_pose_rec`) in the `~/catkin_ws/src` folder.
    - Ensure the package has a valid `package.xml` and `CMakeLists.txt`.

3. Build the Workspace:
   - From the workspace root:

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### Usage

1. Modify the Topic Name:
    - In the code, replace `/natnet_ros/Husky/pose` with your actual topic name that publishes pose data.

2. Run the Node:
    - From the terminal run:
```bash
rosrun husky_pose_recorder pose_recorder.py
```
- (Ensure the package name matches your actual package folder name.)

3. Optional Arguments:
    - You can adjust sampling and enable live plotting via launch parameters:
```bash
rosrun husky_pose_collect pose_recorder.py _sampling_rate:=30 _plot_live:=true
```

### How it Works

- **ROS Master Detection**
    - Prints the current `ROS_MASTER_URI` to help debug cross-machine setups.

- **Subscription**
    - Subscribes to a ROS topic that publishes pose data as `PoseStamped` messages.

- **Sampling Timer**
    - Logs data at a fixed rate using `rospy.Timer`, defaulting to 60 Hz (configurable).

- **Conversion**
    - Converts quaternion orientation to yaw (Euler angle) using the `tf` library. Only yaw is used.

- **Movement Detection**
    - Logs movement deltas in position and yaw if changes exceed 5 cm or 5 degrees.

- **Data Logging**
    - Writes data to an auto-versioned file (`pose_logs/pose_001.txt`, etc.).
    - Format: `timestamp, x, y, z, yaw`

- **Live Plotting (Optional)**
    - If enabled, shows a 2D live trace of x vs y during recording.
    - At shutdown, saves a snapshot of the plot as `pose_001_plot.png`, etc.

### Testing without Lab Data

If you don't have live pose data available, you can simulate data using:
```bash
rostopic pub /natnet_ros/Husky/pose geometry_msgs/PoseStamped "{header: {stamp: now, frame_id: 'base_link'}, pose: {position: {x: 1.0, y: 2.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}" -r 1
```
This command publishes dummy pose data at 1 Hz, allowing you to verify that your node records the data correctly.

### Testing Wireless Interface

Use the `dummy_publisher.py` file to test the network and confirm that the wireless connection between nodes is working.
