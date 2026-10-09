#!/usr/bin/env python3
"""功能分支: 机器人模型发布.

	作用:
	用 xacro 展开 model_file 并启动 robot_state_publisher,
	发布 /robot_description 主题与机器人 TF.

	启动参数:
	model_file 指定机器人模型 xacro 文件,
	默认 <robot_gazebo>/urdf/robot_gazebo.urdf.xacro(含 Gazebo 插件).
	use_sim_time 是否使用仿真时间(依赖 /clock), 默认 true.

	说明:
	本文件是被 gazebo.launch.py 引入的功能分支, 需在 gazebo_robot 分支之前启动,
	保证 /robot_description 就绪后再生成模型.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
	# 1. 文件路径
	pkg_share = get_package_share_directory('robot_gazebo')
	default_model = os.path.join(
		pkg_share, 'urdf', 'robot_gazebo.urdf.xacro'
	)

	# 2. 启动参数
	declare_model_file = DeclareLaunchArgument(
		'model_file',
		default_value=default_model,
		description='机器人模型 xacro 文件路径'
	)
	declare_use_sim_time = DeclareLaunchArgument(
		'use_sim_time',
		default_value='true',
		description='是否使用仿真时间(依赖 /clock)'
	)

	model_file = LaunchConfiguration('model_file')
	use_sim_time = LaunchConfiguration('use_sim_time')

	# 3. 模型描述和节点
	# 必须用 ParameterValue(..., value_type=str) 包一层,
	# 否则 launch_ros 会把 Command 的结果当 YAML 解析而报错.
	robot_description = ParameterValue(
		Command(['xacro "', model_file, '"']),
		value_type=str
	)

	robot_state_publisher = Node(
		package='robot_state_publisher',
		executable='robot_state_publisher',
		name='robot_state_publisher',
		output='screen',
		parameters=[{
			'robot_description': robot_description,
			'use_sim_time': use_sim_time,
		}]
	)

	# 4. 组装启动描述
	return LaunchDescription([
		declare_model_file,
		declare_use_sim_time,
		robot_state_publisher,
	])
