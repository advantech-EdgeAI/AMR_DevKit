from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

from ament_index_python.packages import get_package_share_directory
from launch.logging import get_logger

import os
import yaml

logger = get_logger("platform_bringup")

# -------------------------------------------------
# Window / corner layout (shared)
# -------------------------------------------------
WINDOW_KEYS = [
    "front_upper_window", "front_lower_window",
    "rear_upper_window",  "rear_lower_window",
    "right_upper_window", "right_lower_window",
    "left_upper_window",  "left_lower_window",
]

CORNER_KEYS = [
    "front_right_corner", "front_left_corner",
    "rear_right_corner",  "rear_left_corner",
]

ALL_KEYS = WINDOW_KEYS + CORNER_KEYS

# -------------------------------------------------
# Schemas
# -------------------------------------------------
SCHEMAS = {
    "windows": ["none", "plain", "Gemini335L", "SHF3L"],
    "corners": ["none", "rplidar"],
}

# -------------------------------------------------
# Validation + runtime setup
# -------------------------------------------------
def setup_arguments(context, *args, **kwargs):
    mode = LaunchConfiguration("mode").perform(context)

    pkg = f"{mode}_description"
    share = get_package_share_directory(pkg)

    with open(os.path.join(share, "config", "sensors.yaml"), "r") as f:
        defaults = yaml.safe_load(f)

    actions = []

    for key in ALL_KEYS:
        default = defaults.get(key, {}).get("type", "none")
        actions.append(
            DeclareLaunchArgument(
                key,
                default_value=default,
            )
        )

    return actions

def setup_visualization(context, *args, **kwargs):
    mode = LaunchConfiguration("mode").perform(context)
    pkg = f"{mode}_description"
    share = get_package_share_directory(pkg)
    return [
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", os.path.join(share, "config", "display.rviz")],
            output="screen",
            condition=IfCondition(LaunchConfiguration("display_rviz")),
        ),
        Node(
            package="foxglove_bridge",
            executable="foxglove_bridge",
            name="foxglove_bridge",
            output="screen",
            condition=IfCondition(LaunchConfiguration("foxglove")),
        ),
    ]

def setup_platform(context, *args, **kwargs):
    mode = LaunchConfiguration("mode").perform(context)
    if mode not in ("devkit", "amr"):
        raise RuntimeError("mode must be 'devkit' or 'amr'")

    pkg = f"{mode}_description"
    share = get_package_share_directory(pkg)

    # Load YAML defaults
    config_path = os.path.join(share, "config", "sensors.yaml")
    with open(config_path, "r") as f:
        defaults = yaml.safe_load(f)

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------
    if mode  == "devkit":
        for key in ALL_KEYS:
            value = LaunchConfiguration(key).perform(context)

            if key in WINDOW_KEYS:
                allowed = SCHEMAS["windows"]
            else:
                allowed = SCHEMAS["corners"]

            if value not in allowed:
                raise RuntimeError(
                    f"[{mode}] Invalid value '{value}' for '{key}', allowed={allowed}"
                )

    logger.info(f"[{mode}] sensor layout validated")

    # -------------------------------------------------
    # Build xacro args
    # -------------------------------------------------
    xacro_args = []
    for key in ALL_KEYS:
        xacro_args.extend([
            f" {key}:=",
            LaunchConfiguration(key)
        ])

    urdf_file = f"{mode}.urdf.xacro"

    robot_state_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": ParameterValue(
                Command([
                    "xacro ",
                    PathJoinSubstitution([
                        FindPackageShare(pkg),
                        "urdf",
                        urdf_file
                    ]),
                    *xacro_args
                ]),
                value_type=str,
            )
        }],
    )

    return [robot_state_node]


# -------------------------------------------------
# Launch description
# -------------------------------------------------
def generate_launch_description():
    ld = LaunchDescription()

    # Arguments
    ld.add_action(DeclareLaunchArgument("mode", default_value="devkit", description="Launch mode: devkit | amr"))
    ld.add_action(DeclareLaunchArgument("display_rviz", default_value="false", description="Start RViz"))
    ld.add_action(DeclareLaunchArgument("foxglove", default_value="false", description="Start foxglove bridge"))

    # Runtime validation + node creation
    ld.add_action(OpaqueFunction(function=setup_arguments))
    ld.add_action(OpaqueFunction(function=setup_visualization))
    ld.add_action(OpaqueFunction(function=setup_platform))

    return ld
 