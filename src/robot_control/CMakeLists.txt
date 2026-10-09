cmake_minimum_required(VERSION 3.10)
project(robot_control)

find_package(ament_cmake REQUIRED)

install(
	DIRECTORY
		config/
	DESTINATION share/${PROJECT_NAME}/config
)

install(
	DIRECTORY
		urdf/
	DESTINATION share/${PROJECT_NAME}/urdf
)

ament_package()
