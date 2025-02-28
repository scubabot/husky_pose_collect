#!/usr/bin/env python3
"""
Dummy Publisher for Pose Data

This script creates and publishes dummy pose data (using PoseStamped messages)
on the topic 'caleb_pose_topic'. This allows testing of the wireless network interface
by having this machine publish data while the Jetson on the Husky subscribes to it.
"""

import rospy
from geometry_msgs.msg import PoseStamped

def dummy_publisher():
    # Initialize the ROS node with the name 'dummy_pose_publisher'
    rospy.init_node('dummy_pose_publisher', anonymous=True)
    
    # Create a publisher that sends PoseStamped messages on 'caleb_pose_topic'
    pub = rospy.Publisher('caleb_pose_topic', PoseStamped, queue_size=10)
    
    # Set the publishing rate (1 message per second)
    rate = rospy.Rate(1)
    
    while not rospy.is_shutdown():
        # Create a new PoseStamped message
        pose_msg = PoseStamped()
        # Set the current time as the header timestamp
        pose_msg.header.stamp = rospy.Time.now()
        # Set the frame ID (can be any string; 'base_link' is common)
        pose_msg.header.frame_id = "base_link"
        
        # Set dummy position values
        pose_msg.pose.position.x = 1.0
        pose_msg.pose.position.y = 2.0
        pose_msg.pose.position.z = 0.0
        
        # Set dummy orientation values (this quaternion represents no rotation)
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = 0.0
        pose_msg.pose.orientation.w = 1.0
        
        # Log a message to show that data is being published
        rospy.loginfo("Publishing dummy pose data: x=1.0, y=2.0, z=0.0")
        
        # Publish the message
        pub.publish(pose_msg)
        
        # Sleep to maintain the rate of 1 Hz
        rate.sleep()

if __name__ == '__main__':
    try:
        dummy_publisher()
    except rospy.ROSInterruptException:
        pass
