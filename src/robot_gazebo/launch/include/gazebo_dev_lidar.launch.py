#!/usr/bin/env python3
"""功能分支: 雷达坐标系静态 TF.

	作用:
	把 Gazebo 点云使用的坐标系 <model>/<link>/<sensor> 连接到 URDF 的 laser_link.
	当前雷达 sensor pose 为全零, 因此使用单位变换.

	启动参数:
	无.

	说明:
	本文件是被 gazebo.launch.py 引入的功能分支; 只有在 Gazebo 中生成模型
	(即 sensor 作用域坐标系存在) 之后才有意义.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
	# 1. 节点
	# 将 Gazebo 点云使用的坐标系连接到 URDF 的 laser_link.
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

	# 2. 组装启动描述
	return LaunchDescription([
		c32_static_tf,
	])
