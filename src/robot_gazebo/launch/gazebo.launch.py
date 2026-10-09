#!/usr/bin/env python3
"""Gazebo (Fortress) 四轮差速小车仿真总入口.

	分层结构:
	本文件只负责组合 include/ 下的六个功能分支, 以及 RViz:
	include/robot_description.launch.py  发布 /robot_description 与 TF
	include/gazebo_world.launch.py       启动 Gazebo(server / client)
	include/gazebo_robot.launch.py       把模型生成到 Gazebo 中
	include/bridge.launch.py             Gazebo 与 ROS 2 的话题桥接
	include/control.launch.py            ros2_control 控制器加载
	include/gazebo_dev_lidar.launch.py   雷达坐标系静态 TF

	启动顺序:
	gazebo_world -> robot_description -> gazebo_robot -> bridge -> control
	-> gazebo_dev_lidar -> rviz.
	gazebo_robot 需要 /robot_description 就绪, control 需要 Gazebo 侧的
	controller_manager 就绪, 后者的等待由 spawner 的超时参数保证.

	用法:
	ros2 launch robot_gazebo gazebo.launch.py
	ros2 launch robot_gazebo gazebo.launch.py gui:=false rviz:=false
	ros2 launch robot_gazebo gazebo.launch.py world:="$(pwd)/src/robot_gazebo/worlds/lidar_test.sdf"

	控制器已重映射到标准 /cmd_vel:
	ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
	# 1. 路径
	pkg_share = get_package_share_directory('robot_gazebo')
	include_dir = os.path.join(pkg_share, 'launch', 'include')
	rviz_config = os.path.join(pkg_share, 'rviz', 'gazebo.rviz')
	default_world = os.path.join(pkg_share, 'worlds', 'lidar_test.sdf')
	default_model = os.path.join(pkg_share, 'urdf', 'robot_gazebo.urdf.xacro')

	# 2. 启动参数
	# 与 include/ 下各分支同名, 这里集中声明并向下传递,
	# 分支自身保留默认值, 便于单独运行调试.
	declare_use_sim_time = DeclareLaunchArgument(
		'use_sim_time',
		default_value='true',
		description='节点使用仿真时间(依赖 /clock 桥接)'
	)
	declare_world = DeclareLaunchArgument(
		'world',
		default_value=default_world,
		description='Gazebo world 文件(.sdf)'
	)
	declare_gui = DeclareLaunchArgument(
		'gui',
		default_value='true',
		description='是否启动 Gazebo 图形界面, false 表示 headless'
	)
	declare_gz_version = DeclareLaunchArgument(
		'gz_version',
		default_value='6',
		description='Gazebo 主版本, 6 = Fortress'
	)
	declare_spawn_z = DeclareLaunchArgument(
		'spawn_z',
		default_value='0.10',
		description='模型生成高度'
	)
	declare_model_file = DeclareLaunchArgument(
		'model_file',
		default_value=default_model,
		description='机器人模型 xacro 文件路径'
	)
	declare_rviz = DeclareLaunchArgument(
		'rviz',
		default_value='true',
		description='是否启动 RViz'
	)

	use_sim_time = LaunchConfiguration('use_sim_time')
	world = LaunchConfiguration('world')
	gui = LaunchConfiguration('gui')
	gz_version = LaunchConfiguration('gz_version')
	spawn_z = LaunchConfiguration('spawn_z')
	model_file = LaunchConfiguration('model_file')
	rviz = LaunchConfiguration('rviz')

	def include_branch(name, launch_arguments=None):
		"""引入 include/ 下的功能分支."""
		return IncludeLaunchDescription(
			PythonLaunchDescriptionSource(os.path.join(include_dir, name)),
			launch_arguments=(launch_arguments or {}).items(),
		)

	# 3. 六个功能分支
	branch_gazebo_world = include_branch('gazebo_world.launch.py', {
		'world': world,
		'gui': gui,
		'gz_version': gz_version,
	})
	branch_robot_description = include_branch('robot_description.launch.py', {
		'model_file': model_file,
		'use_sim_time': use_sim_time,
	})
	branch_gazebo_robot = include_branch('gazebo_robot.launch.py', {
		'spawn_z': spawn_z,
	})
	branch_bridge = include_branch('bridge.launch.py')
	branch_control = include_branch('control.launch.py')
	branch_gazebo_dev_lidar = include_branch('gazebo_dev_lidar.launch.py')

	# 4. RViz
	rviz_node = Node(
		package='rviz2',
		executable='rviz2',
		name='rviz2',
		output='screen',
		arguments=['-d', rviz_config],
		parameters=[{'use_sim_time': use_sim_time}],
		condition=IfCondition(rviz),
	)

	# 5. 组装启动描述
	return LaunchDescription([
		declare_use_sim_time,
		declare_world,
		declare_gui,
		declare_gz_version,
		declare_spawn_z,
		declare_model_file,
		declare_rviz,
		branch_gazebo_world,
		branch_robot_description,
		branch_gazebo_robot,
		branch_bridge,
		branch_control,
		branch_gazebo_dev_lidar,
		rviz_node,
	])
