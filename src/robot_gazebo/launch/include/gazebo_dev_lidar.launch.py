#!/usr/bin/env python3
"""功能分支: 雷达点云接入与 2D 激光转换.

	作用:
	1. 坐标系规范化: Gazebo 点云自带坐标系是 <model>/<link>/<sensor>,
	   即 four_wheel_diff_robot/base_link/c32_lidar, 用静态 TF 接到 URDF 的 laser_link,
	   使点云与 TF 树符合 ROS 的惯用结构.
	2. 启动 pointcloud_to_laserscan 把点云压成 2D 激光, 并负责其 ROS 话题映射:
	   输入 cloud_in <- /points_raw(由 bridge 分支桥接得到), 输出 scan -> /scan.

	启动参数:
	target_frame 激光转换的目标坐标系, 默认 laser_link.
	min_height / max_height 参与转换的高度区间, 默认 -0.2 / 0.2,
	用于从 32 线点云中取近似水平的一层.

	说明:
	本文件是被 gazebo.launch.py 引入的功能分支, 需在 gazebo_robot 与 bridge
	分支之后启动, 只有在 Gazebo 中生成模型(即 sensor 作用域坐标系存在)之后才有数据.
	扫描几何与 C32 雷达参数一致: 360 度 / 2000 点 / 10Hz / 0.15-70m.
	注意 pointcloud_to_laserscan 采用惰性订阅, 需要先有 /scan 的订阅者,
	它才会订阅 /points_raw.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
	# 1. 启动参数
	declare_target_frame = DeclareLaunchArgument(
		'target_frame',
		default_value='laser_link',
		description='激光转换的目标坐标系'
	)
	declare_min_height = DeclareLaunchArgument(
		'min_height',
		default_value='-0.2',
		description='参与转换的最小高度(目标坐标系下)'
	)
	declare_max_height = DeclareLaunchArgument(
		'max_height',
		default_value='0.2',
		description='参与转换的最大高度(目标坐标系下)'
	)

	target_frame = LaunchConfiguration('target_frame')
	min_height = LaunchConfiguration('min_height')
	max_height = LaunchConfiguration('max_height')

	# 2. 坐标系规范化: Gazebo 作用域坐标系 -> URDF 的 laser_link
	# 当前雷达 sensor pose 为全零, 因此使用单位变换.
	c32_static_tf = Node(
		package='tf2_ros',
		executable='static_transform_publisher',
		name='c32_static_tf',
		arguments=[
			'--x', '0',
			'--y', '0',
			'--z', '0',
			'--roll', '0',
			'--pitch', '0',
			'--yaw', '0',
			'--frame-id', 'laser_link',
			'--child-frame-id',
			'four_wheel_diff_robot/base_link/c32_lidar',
		],
		output='screen',
	)

	# 3. 点云 -> 2D 激光(含 ROS 话题映射)
	pointcloud_to_laserscan = Node(
		package='pointcloud_to_laserscan',
		executable='pointcloud_to_laserscan_node',
		name='pointcloud_to_laserscan',
		remappings=[
			('cloud_in', '/points_raw'),
			('scan', '/scan'),
		],
		parameters=[{
			'target_frame': target_frame,
			'transform_tolerance': 0.01,
			'min_height': ParameterValue(min_height, value_type=float),
			'max_height': ParameterValue(max_height, value_type=float),
			# 与 C32 雷达一致: 360 度 / 2000 点 / 10Hz / 0.15-70m
			'angle_min': -3.14159265,
			'angle_max': 3.14159265,
			'angle_increment': 0.00314159,
			'scan_time': 0.1,
			'range_min': 0.15,
			'range_max': 70.0,
			'use_inf': True,
			'inf_epsilon': 1.0,
		}],
		output='screen',
	)

	# 4. 组装启动描述
	return LaunchDescription([
		declare_target_frame,
		declare_min_height,
		declare_max_height,
		c32_static_tf,
		pointcloud_to_laserscan,
	])
