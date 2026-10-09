#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.conditions import IfCondition


def generate_launch_description():
	pkg_dir = get_package_share_directory('robot_description')

	# --- Paths
	xacro_file = os.path.join(pkg_dir, 'urdf', 'robot_description.urdf.xacro')
	rviz_config = os.path.join(pkg_dir, 'rviz', 'description.rviz')

	# --- Launch arguments
	use_sim_time = LaunchConfiguration('use_sim_time', default='false')
	gui = LaunchConfiguration('gui', default='true')

	declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='false', description='Use simulation time')
	declare_gui = DeclareLaunchArgument('gui', default_value='true', description='Enable GUI components')

	# --- Nodes
	robot_state_pub = Node(
		package='robot_state_publisher',
		executable='robot_state_publisher',
		name='robot_state_publisher',
		output='screen',
		parameters=[{
			'robot_description': ParameterValue(
				Command(['xacro ', xacro_file]), value_type=str),
			'use_sim_time': use_sim_time
		}]
	)

	joint_state_pub = Node(
		package='joint_state_publisher_gui',
		executable='joint_state_publisher_gui',
		name='joint_state_publisher_gui',
		output='screen'
	)

	# RViz
	rviz_node = Node(
		package='rviz2',
		executable='rviz2',
		name='rviz2',
		output='screen',
		arguments=['-d', rviz_config],
		condition=IfCondition(gui)
	)

	# --- Launch Description
	ld = LaunchDescription()
	ld.add_action(declare_use_sim_time)
	ld.add_action(declare_gui)
	ld.add_action(robot_state_pub)
	ld.add_action(joint_state_pub)
	if rviz_node:
		ld.add_action(rviz_node)

	return ld
