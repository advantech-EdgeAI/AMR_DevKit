from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os
import yaml
import math

from launch.logging import get_logger
logger = get_logger('my_launch')

# ------------------------
# Schemas
# ------------------------
STRICT_SCHEMAS = {
    "SHF3L": {"required": ["camera_serial"], "optional": []},
    "Gemini335L": {"required": ["usb_port"], "optional": []},
    "rplidar": {"required": ["udp_ip"], "optional": []},
}

PERMISSIVE_SCHEMAS = {
    "none": {"required": [], "optional": []},
    "plain": {"required": [], "optional": []},
    "SHF3L": {"required": [], "optional": ["camera_serial"]},
    "Gemini335L": {"required": [], "optional": ["usb_port"]},
    "rplidar": {"required": [], "optional": ["udp_ip"]},
}

def get_schema(mode: str):
    return STRICT_SCHEMAS if mode == "amr" else PERMISSIVE_SCHEMAS

# ------------------------
# Config validation
# ------------------------
def validate_config(config, schemas):
    for name, cfg in config.items():
        if "type" not in cfg:
            raise RuntimeError(f"[{name}] missing required key: 'type'")
        sensor_type = cfg["type"]
        if sensor_type not in schemas:
            raise RuntimeError(f"[{name}] unknown type '{sensor_type}', allowed: {list(schemas.keys())}")
        schema = schemas[sensor_type]
        for key in schema["required"]:
            if key not in cfg:
                raise RuntimeError(f"[{name}] type '{sensor_type}' requires '{key}'")
        allowed_keys = {"type"} | set(schema["required"]) | set(schema["optional"])
        for key in cfg.keys():
            if key not in allowed_keys:
                raise RuntimeError(f"[{name}] key '{key}' not allowed for type '{sensor_type}'")

# ------------------------
# Stage 1 + Stage 2 merged safely
# ------------------------
def setup_visualization(context, *args, **kwargs):
    mode = LaunchConfiguration("mode").perform(context)
    pkg = f"{mode}_description"
    share = get_package_share_directory(pkg)
    return [
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", os.path.join(share, "config", "bringup.rviz")],
            output="screen",
            condition=IfCondition(LaunchConfiguration("bringup_rviz")),
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", os.path.join(share, "config", "yolo.rviz")],
            output="screen",
            condition=IfCondition(LaunchConfiguration("yolo_rviz")),
        ),
        Node(
            package="foxglove_bridge",
            executable="foxglove_bridge",
            name="foxglove_bridge",
            output="screen",
            condition=IfCondition(LaunchConfiguration("foxglove")),
        ),
    ]

def setup_sensors(context, *args, **kwargs):
    mode = LaunchConfiguration('mode').perform(context)
    if mode not in ("amr", "devkit"):
        raise RuntimeError("mode must be 'amr' or 'devkit'")

    pkg = f"{mode}_description"
    share = get_package_share_directory(pkg)
    config_path = os.path.join(share, "config", "sensors.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    schemas = get_schema(mode)
    validate_config(config, schemas)

    nodes = []

    # Preprocess launch
    preprocess = LaunchConfiguration('preprocess').perform(context)
    if preprocess.lower() == "true":
        logger.info("Launching sensor preprocess pipeline")
        nodes.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(
                        get_package_share_directory("sensor_launch"),
                        "launch",
                        "sensor_preprocess.launch.py",
                    )
                ),
                launch_arguments={
                    "sensors_config": config_path,
                }.items(),
            )
        )
        
    # Count Gemini cameras for device_num
    gemini_count = sum(1 for _, cfg in config.items() if cfg.get("type") == "Gemini335L" and "usb_port" in cfg)

    for name, cfg in config.items():
        sensor_type = cfg.get("type")

        if sensor_type in ("none", "plain"):
            continue

        # ---------- Gemini ----------
        if sensor_type == "Gemini335L" and "usb_port" in cfg:
            nodes.append(
                Node(
                    package="tf2_ros",
                    executable="static_transform_publisher",
                    name=f"{name}_tf",
                    arguments=["0", "0", "0", f"{-math.pi/2}", "0", "0", f"{name}_mount", f"{name}_link"],
                )
            )

            nodes.append(
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(
                            get_package_share_directory("orbbec_camera"),
                            "launch",
                            "gemini_330_series.launch.py",
                        )
                    ),
                    launch_arguments={
                        "camera_name": name,
                        "usb_port": cfg["usb_port"],
                        "device_num": str(gemini_count),
                        "sync_mode": "secondary_synced",
                    }.items(),
                )
            )

        # ---------- SHF3L ----------
        elif sensor_type == "SHF3L" and "camera_serial" in cfg:
            nodes.append(
                Node(
                    package="sensor_launch",
                    executable="camera_v4l2",
                    name=f"{name}_camera",
                    namespace=name,
                    parameters=[{"camera_serial": cfg["camera_serial"]}],
                )
            )

        # ---------- RPLIDAR ----------
        elif sensor_type == "rplidar" and "udp_ip" in cfg:
            nodes.append(
                Node(
                    package="sllidar_ros2",
                    executable="sllidar_node",
                    name=f"{name}_sllidar",
                    namespace=name,
                    parameters=[{
                        "channel_type": "udp",
                        "udp_ip": cfg["udp_ip"],
                        "udp_port": 8089,
                        "frame_id": f"{name}_mount",
                    }],
                )
            )
    
    return nodes

# ------------------------
# Launch description
# ------------------------
def generate_launch_description():
    ld = LaunchDescription()

    # Arguments
    ld.add_action(DeclareLaunchArgument("mode", default_value="devkit", description="Launch mode: amr | devkit"))
    ld.add_action(DeclareLaunchArgument("bringup_rviz", default_value="false", description="Start RViz"))
    ld.add_action(DeclareLaunchArgument("yolo_rviz", default_value="false", description="Start RViz for yolo"))
    ld.add_action(DeclareLaunchArgument("foxglove", default_value="false", description="Start foxglove bridge"))
    ld.add_action(DeclareLaunchArgument("preprocess", default_value="false", description="Enable preprocess pipeline"))

    # Stage 1 + Stage 2: validate and create nodes safely
    ld.add_action(OpaqueFunction(function=setup_visualization))
    ld.add_action(OpaqueFunction(function=setup_sensors))

    # Display launch
    share = get_package_share_directory("devkit_description")
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(get_package_share_directory("devkit_description"), "launch", "display.launch.py")),
            launch_arguments={"display_rviz": "false"}.items(),
        )
    )

    return ld
