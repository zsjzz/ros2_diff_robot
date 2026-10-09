#!/usr/bin/env python3
"""Gazebo (Fortress) 仿真 bringup.

	用法:
	ros2 launch robot_gazebo gazebo.launch.py
	ros2 launch robot_gazebo gazebo.launch.py world:="$(pwd)/src/robot_gazebo/worlds/lidar_test.sdf"

	控制器已重映射到标准 /cmd_vel:
	ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import os

from ament_index_python.packages import get_package_prefix
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
	# --- 1. 路径
	pkg_share = get_package_share_directory('robot_gazebo')
	ros_gz_sim_share = get_package_share_directory('ros_gz_sim')
	rviz_config = os.path.join(pkg_share, 'rviz', 'gazebo.rviz')

	robot_xacro = os.path.join(pkg_share, 'urdf', 'robot_gazebo.urdf.xacro')
	world_file = os.path.join(pkg_share, 'worlds', 'lidar_test.sdf')

	# Gazebo 解析 mesh 时会把 package:// 转成 model://,需要把各包 share 的父目录
	# 加进资源搜索路径,否则 mesh 加载失败,模型没有碰撞体会直接掉下去.
	# gz_sim.launch.py 在运行时直接读 os.environ,所以这里设置进去.
	existing = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
	pkgs = ('robot_description', 'robot_gazebo')
	resource_paths = [os.path.join(get_package_prefix(p), 'share') for p in pkgs]
	if existing:
		resource_paths.append(existing)
	resource_paths = os.pathsep.join(resource_paths)
	os.environ['GZ_SIM_RESOURCE_PATH'] = resource_paths
	os.environ['IGN_GAZEBO_RESOURCE_PATH'] = resource_paths

	# --- 2. 可选的启动参数
	declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='true',
		description='节点使用仿真时间(依赖 /clock 桥接)')
	declare_gz_version = DeclareLaunchArgument('gz_version', default_value='6',
		description='Gazebo 主版本.6=Fortress(本机 ROS 侧工具链只支持 Fortress)')
	declare_world = DeclareLaunchArgument('world', default_value=world_file,
		description='Gazebo world 文件(.sdf)')
	declare_gui = DeclareLaunchArgument('gui', default_value='true',
		description='是否启动 Gazebo 图形界面.false => 只跑 server(headless)')
	declare_spawn_z = DeclareLaunchArgument('spawn_z', default_value='0.10',
		description='模型生成高度.轮子最低点在 base_link 下方 0.09m,抬高 0.1m 避免轮子一开始就陷进地面')
	declare_rviz = DeclareLaunchArgument('rviz', default_value='true', 
		description='是否启动 RViz')

	use_sim_time = LaunchConfiguration('use_sim_time')
	gz_version = LaunchConfiguration('gz_version')
	world = LaunchConfiguration('world')
	gui = LaunchConfiguration('gui')
	spawn_z = LaunchConfiguration('spawn_z')
	rviz = LaunchConfiguration('rviz')

	# --- 3. 节点

	# 组合描述:geometry(robot_description) + ros2_control(robot_control) + Gazebo 插件
	# 注意:必须用 ParameterValue(..., value_type=str) 包一层,
	#       否则 launch_ros 会把 Command 的结果当 YAML 解析而报错
	robot_description = ParameterValue(Command(['xacro ', robot_xacro]), value_type=str)

	robot_state_publisher = Node(
		package='robot_state_publisher',
		executable='robot_state_publisher',
		name='robot_state_publisher',
		output='screen',
		parameters=[{
			'robot_description': robot_description,
			'use_sim_time': use_sim_time,
		}],
	)

	# Gazebo:gz_version=6 时 ros_gz_sim 会自动走 `ign gazebo`(Fortress)
	gz_sim_launch = os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')

	# gui:=true  -> 正常带图形界面启动
	gazebo_with_gui = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(gz_sim_launch),
		launch_arguments={'gz_args': ['-r ', world], 'gz_version': gz_version}.items(),
		condition=IfCondition(gui),
	)
	# gui:=false -> 追加 -s,只跑 server(headless)
	gazebo_headless = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(gz_sim_launch),
		launch_arguments={'gz_args': ['-r -s ', world], 'gz_version': gz_version}.items(),
		condition=IfCondition(PythonExpression(["'", gui, "' == 'false'"])),
	)

	# Gazebo -> ROS 的时钟桥接,ros2_control 与 TF 的 use_sim_time 依赖它
	clock_bridge = Node(
		package='ros_gz_bridge',
		executable='parameter_bridge',
		arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
		output='screen',
	)

	# 把 robot_description 送进 Gazebo(等 robot_state_publisher 发布后再取)
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

	# controller_manager 由 gz_ros2_control 插件在模型生成时创建,
	# 所以必须等 create 进程退出后再加载控制器
	load_joint_state_broadcaster = Node(
		package='controller_manager',
		executable='spawner',
		arguments=['joint_state_broadcaster'],
		output='screen',
	)
	load_diff_drive_controller = Node(
		package='controller_manager',
		executable='spawner',
		arguments=['diff_drive_controller'],
		output='screen',
	)
	load_controllers = RegisterEventHandler(
		OnProcessExit(
			target_action=spawn_robot,
			on_exit=[load_joint_state_broadcaster, load_diff_drive_controller],
		)
	)

	rviz_node = Node(
		package='rviz2',
		executable='rviz2',
		name='rviz2',
		output='screen',
		arguments=['-d', rviz_config],
		parameters=[{'use_sim_time': use_sim_time}],
		condition=IfCondition(rviz),
	)

	c32_bridge = Node(
		package='ros_gz_bridge',
		executable='parameter_bridge',
		name='c32_bridge',
		arguments=[
			'/c32/points@sensor_msgs/msg/PointCloud2'
			'[ignition.msgs.PointCloudPacked',
		],
		remappings=[
			('/c32/points', '/points_raw'),
		],
		output='screen',
	)

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
		output='screen'
	)

	# --- 4. 组装
	return LaunchDescription([
		declare_use_sim_time,
		declare_gz_version,
		declare_world,
		declare_gui,
		declare_spawn_z,
		declare_rviz,
		robot_state_publisher,
		gazebo_with_gui,
		gazebo_headless,
		clock_bridge,
		spawn_robot,
		load_controllers,
		rviz_node,
		c32_bridge,
		c32_static_tf,
	])
