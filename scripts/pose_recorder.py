#!/usr/bin/env python3
import rospy
import os
import math
import glob
import threading
import time

from geometry_msgs.msg import PoseStamped
import tf  # For quaternion -> euler
import matplotlib.pyplot as plt  # For optional live plotting

########################################
# 1) SETUP YOUR LOG DIRECTORY & FILE
########################################

def get_next_log_filename():
    """
    Returns the next available auto-numbered filename in the default pose_logs directory.
    Default path: ~/catkin_ws/src/pose_logs
    """
    log_dir = os.path.expanduser("~/catkin_ws/src/pose_logs")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    existing_logs = glob.glob(os.path.join(log_dir, "pose_*.txt"))
    new_index = len(existing_logs) + 1
    filename = f"pose_{new_index:03d}.txt"
    return os.path.join(log_dir, filename)

########################################
# 2) CONVERT QUATERNION -> YAW
########################################

def quaternion_to_yaw(orientation_q):
    """
    Convert a quaternion (orientation) into a yaw angle in radians.
    """
    quaternion = (
        orientation_q.x,
        orientation_q.y,
        orientation_q.z,
        orientation_q.w
    )
    # This returns (roll, pitch, yaw)
    euler = tf.transformations.euler_from_quaternion(quaternion)
    return euler[2]

########################################
# 3) GLOBALS FOR LOGGING & PLOTTING
########################################

LOG_FILE = None         # Path to the output file
start_time = None       # Time we started logging
last_report_time = None # For summary stats once per second
poses_logged = 0        # Total lines logged

# We'll store the latest pose in these globals
latest_pose = None
latest_pose_received = False

# We'll keep track of the last logged pose to detect movement
last_logged_x = None
last_logged_y = None
last_logged_yaw = None

# Thresholds for "significant" motion
DIST_THRESHOLD = 0.05   # 5 cm
YAW_THRESHOLD  = math.radians(5.0)  # 5 degrees

# For optional live plotting
plot_live = False
plot_data = {
    'x': [],
    'y': []
}
plot_thread = None
plot_shutdown = False
plot_fig = None
plot_ax = None

########################################
# 4) SUBSCRIBER CALLBACK: STORE POSE
########################################

def pose_callback(msg):
    global latest_pose, latest_pose_received

    # Simply store the latest pose, do not log here.
    latest_pose = msg
    latest_pose_received = True

########################################
# 5) TIMER CALLBACK: LOG POSE
########################################

def timer_callback(event):
    global start_time, last_report_time, poses_logged
    global last_logged_x, last_logged_y, last_logged_yaw
    global latest_pose_received, latest_pose
    global plot_data

    now = rospy.Time.now().to_sec()

    # If we haven't started the timer or last_report_time, do it now
    if start_time is None:
        start_time = now
        last_report_time = now

    # We only log if we've received at least one pose
    if not latest_pose_received or latest_pose is None:
        return

    # Grab the latest pose data safely
    msg = latest_pose
    x = msg.pose.position.x
    y = msg.pose.position.y
    z = msg.pose.position.z
    yaw = quaternion_to_yaw(msg.pose.orientation)

    # Time stamp from message
    time_stamp = msg.header.stamp.to_sec()
    if time_stamp == 0.0:
        time_stamp = now

    # Write data line to file
    data_line = "{:.3f},{:.4f},{:.4f},{:.4f},{:.4f}\n".format(time_stamp, x, y, z, yaw)
    with open(LOG_FILE, "a") as f:
        f.write(data_line)

    # Update count
    poses_logged += 1

    # Movement detection compared to last logged
    if last_logged_x is not None and last_logged_y is not None and last_logged_yaw is not None:
        dist = math.sqrt((x - last_logged_x)**2 + (y - last_logged_y)**2)
        dyaw = abs(yaw - last_logged_yaw)
        if dyaw > math.pi:
            dyaw = 2*math.pi - dyaw

        if dist >= DIST_THRESHOLD or dyaw >= YAW_THRESHOLD:
            rospy.loginfo(f"ΔPos = {dist:.3f}m | ΔYaw = {math.degrees(dyaw):.1f}° — pose recorded.")

    # Update "last logged" values
    last_logged_x = x
    last_logged_y = y
    last_logged_yaw = yaw

    # For live plotting
    if plot_live:
        plot_data['x'].append(x)
        plot_data['y'].append(y)

    # Print summary stats once per second
    if (now - last_report_time) >= 1.0:
        elapsed = now - start_time
        rate = poses_logged / elapsed if elapsed > 0 else 0
        rospy.loginfo(f"Logged {poses_logged} poses | Elapsed: {elapsed:.2f}s | Avg rate: {rate:.1f} Hz")
        last_report_time = now

########################################
# 6) LIVE PLOTTING THREAD (OPTIONAL)
########################################

def live_plot_thread():
    """
    Runs in a separate thread if plot_live==True.
    Updates the plot every ~0.5 seconds.
    """
    global plot_fig, plot_ax
    plt.ion()
    plot_fig, plot_ax = plt.subplots()
    line, = plot_ax.plot([], [], 'o-')  # A simple 2D trace line

    while not plot_shutdown and not rospy.is_shutdown():
        # Copy data for thread safety
        x_vals = plot_data['x'][:]
        y_vals = plot_data['y'][:]

        if x_vals and y_vals:
            line.set_xdata(x_vals)
            line.set_ydata(y_vals)
            plot_ax.relim()
            plot_ax.autoscale_view()
        plt.draw()
        plt.pause(0.1)
        time.sleep(0.4)  # ~0.5 sec total loop time

    # Save final plot before closing
    if plot_fig:
        image_filename = LOG_FILE.replace(".txt", "_plot.png")
        plot_fig.savefig(image_filename)
        rospy.loginfo(f"Saved final plot to {image_filename}")

    plt.ioff()
    plt.close(plot_fig)

########################################
# 7) MAIN ROS SETUP
########################################

def main():
    global LOG_FILE, plot_live, plot_thread

    rospy.init_node('pose_recorder', anonymous=True)

    # 7a) Check ROS_MASTER_URI
    ros_master_uri = os.getenv('ROS_MASTER_URI', 'Not set')
    rospy.loginfo(f"ROS_MASTER_URI is: {ros_master_uri}")

    # 7b) Create next log file
    LOG_FILE = get_next_log_filename()
    rospy.loginfo(f"Logging pose data to: {LOG_FILE}")

    # 7c) Read optional params
    #     e.g. rosrun your_pkg pose_recorder.py _plot_live:=true _sampling_rate:=30

    global plot_live
    plot_live = rospy.get_param('~plot_live', False)
    sampling_rate = rospy.get_param('~sampling_rate', 60.0)  # Default 60 Hz

    if plot_live:
        rospy.loginfo("Live plotting is ENABLED. A matplotlib window will open.")

    # 7d) Subscribe to the pose topic
    rospy.Subscriber("/natnet_ros/Husky/pose", PoseStamped, pose_callback)

    # 7e) Start a Timer to log at 'sampling_rate' (Hz)
    rospy.Timer(rospy.Duration(1.0 / sampling_rate), timer_callback)

    # 7f) If live plotting, start thread
    if plot_live:
        global plot_thread
        plot_thread = threading.Thread(target=live_plot_thread)
        plot_thread.start()

    # 7g) Spin to keep script running
    rospy.spin()

    # Once rospy.spin() exits, we should cleanly shut down the plot
    if plot_live:
        global plot_shutdown
        plot_shutdown = True
        plot_thread.join()

if __name__ == '__main__':
    main()

