
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml

def launch_setup(context, *args, **kwargs):
    config_path = LaunchConfiguration('sensors_config').perform(context)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    nodes = []

    for name, cfg in config.items():
        if cfg['type'] == 'Gemini335L':
            nodes.append(
                Node(
                    package='sensor_launch',
                    executable='camera_resize',
                    name=f'{name}_camera_resizer',
                    parameters=[
                        {'camera_prefix': name}
                    ]
                )
            )

            nodes.append(
                Node(
                    package='sensor_launch',
                    executable='pointcloud_downsample',
                    name=f'{name}_pointcloud_downsampler',
                    remappings=[
                        ('points_in', f'/{name}/depth/points'),
                        ('points_out', f'/{name}/depth/points_downsampled'),
                    ]
                )
            )

    return nodes

def generate_launch_description():
    
    preprocess_arg = DeclareLaunchArgument(
        'sensors_config',
        description='Path to sensors.yaml'
    )

    return LaunchDescription([
        preprocess_arg,
        OpaqueFunction(function=launch_setup)
    ])