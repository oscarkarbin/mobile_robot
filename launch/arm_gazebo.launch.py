import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, RegisterEventHandler 
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import (OnExecutionComplete, OnProcessExit,
                                OnProcessIO, OnProcessStart, OnShutdown)



from launch_ros.actions import Node
import xacro



def generate_launch_description():
    robotXacroName ='robot'

    namePackage = 'mobile_robot'

    modelFileRelativePath = 'model/arm.urdf.xacro'
    
    worldFileRelativePath = 'model/empty_world.world'

    pathModelFile = os.path.join(get_package_share_directory(namePackage),modelFileRelativePath)

    pathWorldFile = os.path.join(get_package_share_directory(namePackage),worldFileRelativePath)

    robotDescription = xacro.process_file(pathModelFile).toxml()

    gazebo_rosPackageLaunch = PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('gazebo_ros'),'launch','gazebo.launch.py'))

    gazeboLaunch = IncludeLaunchDescription(gazebo_rosPackageLaunch, launch_arguments={'world': pathWorldFile}.items())

    spawnModelNode = Node(
        package='gazebo_ros', 
        executable='spawn_entity.py', 
        arguments=['-topic','robot_description','-entity',robotXacroName],
        output='screen'
    )

    nodeRobotStatePublisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robotDescription, 'use_sim_time': True}]
    )

    load_jsc = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'joint_state_broadcaster'],
        output='screen'
    )

    load_ac = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active', 'arm_controller'],
        output='screen'
    )

    LaunchDescriptionObject = LaunchDescription()
    LaunchDescriptionObject.add_action(
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawnModelNode,
                on_exit=[load_jsc],
            )
        )
    )

    LaunchDescriptionObject.add_action(
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_jsc,
                on_exit=[load_ac],
            )
        )
    )
    LaunchDescriptionObject.add_action(gazeboLaunch)
    LaunchDescriptionObject.add_action(spawnModelNode)
    LaunchDescriptionObject.add_action(nodeRobotStatePublisher)

    return LaunchDescriptionObject

