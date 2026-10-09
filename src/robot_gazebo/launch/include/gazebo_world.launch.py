#!/usr/bin/env python3
"""功能分支: 启动 Gazebo 仿真世界.

	作用:
	1. 设置 GZ_SIM_RESOURCE_PATH / IGN_GAZEBO_RESOURCE_PATH, 让 Gazebo 能把
	   package:// 解析到各包的 share 目录, 否则 mesh 加载失败, 模型没有碰撞体
	   会直接掉下去.
	2. 按 gui 参数启动带图形界面或 headless 的 gz_sim.

	启动参数:
	world 指定 world 文件(.sdf), 默认 <robot_gazebo>/worlds/lidar_test.sdf.
	gui 是否启动 Gazebo 图形界面, 默认 true; false 时追加 -s 只跑 server.
	gz_version Gazebo 主版本, 默认 6(Fortress).

	说明:
	本文件是被 gazebo.launch.py 引入的功能分支; 资源路径必须在加载
	gz_sim.launch.py 之前设置, 因为它在运行时直接读取 os.environ.
"""

import os

from ament_index_python.packages import (
	get_package_prefix,
	get_package_share_directory,
)
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
	# 1. 资源搜索路径
	# Gazebo 解析 mesh 时会把 package:// 转成 model://, 需要把各包 share 的
	# 父目录加进资源搜索路径, 否则 mesh 加载失败.
	existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
	packages = ('robot_description', 'robot_gazebo')
	resource_paths = [
		os.path.join(get_package_prefix(package), 'share')
		for package in packages
	]
	if existing:
		resource_paths.append(existing)

	resource_paths = os.pathsep.join(resource_paths)
	os.environ['GZ_SIM_RESOURCE_PATH'] = resource_paths
	os.environ['IGN_GAZEBO_RESOURCE_PATH'] = resource_paths

	# 2. 文件路径与启动参数
	default_world = os.path.join(
		get_package_share_directory('robot_gazebo'),
		'worlds',
		'lidar_test.sdf',
	)
	gz_sim_launch = os.path.join(
		get_package_share_directory('ros_gz_sim'),
		'launch',
		'gz_sim.launch.py',
	)

	declare_world = DeclareLaunchArgument(
		'world',
		default_value=default_world,
		description='Gazebo world 文件(.sdf)'
	)
	declare_gui = DeclareLaunchArgument(
		'gui',
		default_value='true',
		description='是否启动 Gazebo 图形界面, false 表示只跑 server'
	)
	declare_gz_version = DeclareLaunchArgument(
		'gz_version',
		default_value='6',
		description='Gazebo 主版本, 6 = Fortress'
	)

	world = LaunchConfiguration('world')
	gui = LaunchConfiguration('gui')
	gz_version = LaunchConfiguration('gz_version')

	# 3. 节点
	# gui:=true  -> 正常带图形界面启动
	gazebo_with_gui = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(gz_sim_launch),
		launch_arguments={
			'gz_args': ['-r ', world],
			'gz_version': gz_version,
		}.items(),
		condition=IfCondition(gui),
	)

	# gui:=false -> 追加 -s, 只跑 server(headless)
	gazebo_headless = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(gz_sim_launch),
		launch_arguments={
			'gz_args': ['-r -s ', world],
			'gz_version': gz_version,
		}.items(),
		condition=IfCondition(
			PythonExpression(["'", gui, "' == 'false'"])
		),
	)

	# 4. 组装启动描述
	return LaunchDescription([
		declare_world,
		declare_gui,
		declare_gz_version,
		gazebo_with_gui,
		gazebo_headless,
	])
