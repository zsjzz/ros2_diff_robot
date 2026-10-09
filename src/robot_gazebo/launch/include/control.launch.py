#!/usr/bin/env python3
"""功能分支: ros2_control 控制器加载.

	作用:
	在 controller_manager 上加载并激活 joint_state_broadcaster 与
	diff_drive_controller.

	启动参数:
	controller_manager 指定 controller_manager 节点名, 默认 /controller_manager.
	controller_manager_timeout 等待 controller_manager 服务可用的秒数, 默认 60.

	说明:
	controller_manager 由 gz_ros2_control 插件在模型生成时创建, 所以本分支
	应在 gazebo_robot 分支之后启动; spawner 侧的等待超时可保证顺序无关.
	控制器参数由插件通过 robot_control/config/controllers.yaml 注入,
	这里只负责触发加载.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
	# 1. 启动参数
	declare_controller_manager = DeclareLaunchArgument(
		'controller_manager',
		default_value='/controller_manager',
		description='controller_manager 节点名'
	)
	declare_controller_manager_timeout = DeclareLaunchArgument(
		'controller_manager_timeout',
		default_value='60',
		description='等待 controller_manager 服务可用的秒数'
	)

	controller_manager = LaunchConfiguration('controller_manager')
	controller_manager_timeout = LaunchConfiguration(
		'controller_manager_timeout'
	)

	# 2. 控制器加载节点
	def spawner(controller_name):
		return Node(
			package='controller_manager',
			executable='spawner',
			name=controller_name + '_spawner',
			arguments=[
				controller_name,
				'--controller-manager', controller_manager,
				'--controller-manager-timeout', controller_manager_timeout,
			],
			output='screen',
		)

	# 3. 组装启动描述
	return LaunchDescription([
		declare_controller_manager,
		declare_controller_manager_timeout,
		spawner('joint_state_broadcaster'),
		spawner('diff_drive_controller'),
	])
