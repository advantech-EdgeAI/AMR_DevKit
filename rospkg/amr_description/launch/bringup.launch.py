from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='amr', description='Launch mode: amr or devkit'),
        DeclareLaunchArgument('preprocess', default_value='false', description='Enable sensor preprocess pipeline'),
        DeclareLaunchArgument('bringup_rviz', default_value='false', description='Whether to start RViz'),
        DeclareLaunchArgument('yolo_rviz', default_value='false', description='Whether to start RViz for yolo'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('devkit_description'), 'launch', 'bringup.launch.py')
            ),
            launch_arguments={
                'mode': LaunchConfiguration('mode'),
                'preprocess': LaunchConfiguration('preprocess'),
                'bringup_rviz': LaunchConfiguration('bringup_rviz'),
            }.items()
        ),
    ])