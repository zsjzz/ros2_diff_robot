cmake_minimum_required(VERSION 3.10)
project(robot_gazebo)

find_package(ament_cmake REQUIRED)

install(
	DIRECTORY
		launch/
	DESTINATION share/${PROJECT_NAME}/launch
)

install(
	DIRECTORY
		urdf/
	DESTINATION share/${PROJECT_NAME}/urdf
)

install(
	DIRECTORY
		rviz/
	DESTINATION share/${PROJECT_NAME}/rviz
)

install(
	DIRECTORY
		worlds/
	DESTINATION share/${PROJECT_NAME}/worlds
)

ament_package()
