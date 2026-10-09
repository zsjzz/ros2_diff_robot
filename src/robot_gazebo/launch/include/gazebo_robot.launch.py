#!/usr/bin/env python3
"""功能分支: 在 Gazebo 中生成机器人.

	作用:
	用 ros_gz_sim create 从 /robot_description 读取模型并生成到 Gazebo.

	启动参数:
	spawn_z 模型生成高度, 默认 0.10.
	轮子最低点在 base_link 下方 0.09m, 抬高 0.1m 可避免轮子一开始陷进地面.

	说明:
	本文件是被 gazebo.launch.py 引入的功能分支, 需在 robot_description 与
	gazebo_world 分支之后启动.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
	# 1. 启动参数
	declare_spawn_z = DeclareLaunchArgument(
		'spawn_z',
		default_value='0.10',
		description='模型生成高度'
	)

	spawn_z = LaunchConfiguration('spawn_z')

	# 2. 节点
	# 从 ROS 2 的 /robot_description 获取模型, 在 Gazebo 中生成机器人.
	spawn_robot = Node(
		package='ros_gz_sim',
		executable='create',
		arguments=[
			'-name', 'four_wheel_diff_robot',
			'-topic', '/robot_description',
			'-z', spawn_z,
		],
		output='screen',
	)

	# 3. 组装启动描述
	return LaunchDescription([
		declare_spawn_z,
		spawn_robot,
	])
