"""
ROS2 Jazzy launch file for Voxblox cow_and_lady dataset.

This launch file:
- Optionally plays a ROS bag file with clock publishing
- Launches the voxblox tsdf_server node with parameters from config file
- Remaps pointcloud and transform topics

Download the dataset here: https://projects.asl.ethz.ch/datasets/doku.php?id=iros2017
Dataset index: https://projects.asl.ethz.ch/datasets/

If your input is a ROS1 .bag, convert it before launching:
    pip install rosbags --break-system-packages
    rosbags-convert --src data.bag --dst mission_1_jazzy
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
import os
import uuid


def generate_launch_description():
    # Declare launch arguments
    play_bag_arg = DeclareLaunchArgument(
        'play_bag',
        default_value='true',
        description='Whether to play the bag file'
    )

    bag_file_arg = DeclareLaunchArgument(
        'bag_file',
        default_value='/path/to/data.bag',
        description='Path to the ROS bag file'
    )

    voxel_size_arg = DeclareLaunchArgument(
        'voxel_size',
        default_value='0.05',
        description='TSDF voxel size in meters'
    )

    # Get package share directory for output paths
    voxblox_ros_share = get_package_share_directory('voxblox_ros')

    # Generate unique anonymous name for mesh file (similar to $(anon cow))
    # In ROS2, we use Python's uuid to generate a unique identifier
    mesh_output_dir = os.path.join(voxblox_ros_share, 'mesh_results')
    os.makedirs(mesh_output_dir, exist_ok=True)
    mesh_filename = os.path.join(mesh_output_dir, f'cow_{uuid.uuid4().hex[:8]}.ply')

    # ROS bag player process (conditional on play_bag argument)
    bag_player = ExecuteProcess(
        condition=IfCondition(LaunchConfiguration('play_bag')),
        cmd=[
            'ros2', 'bag', 'play',
            LaunchConfiguration('bag_file'),
            '-r', '1.0',
            '--clock'
        ],
        output='screen',
        name='player'
    )

    # Voxblox TSDF server node
    voxblox_node = Node(
        package='voxblox_ros',
        executable='tsdf_server',
        name='voxblox_node',
        output='screen',
        parameters=[
            {
                'tsdf_voxel_size': LaunchConfiguration('voxel_size'),
                'tsdf_voxels_per_side': 16,
                'voxel_carving_enabled': True,
                'color_mode': 'color',
                'update_mesh_every_n_sec': 1.0,
                'min_time_between_msgs_sec': 0.0,
                'method': 'fast',
                'use_const_weight': False,
                'allow_clear': True,
                'verbose': True,
                'publish_pointclouds': True,
                'publish_pointclouds_on_update': True,
                'publish_slices': False,
                'mesh_filename': mesh_filename,
            }
        ],
        remappings=[
            ('pointcloud', '/camera/depth_registered/points'),
            ('voxblox_node/pointcloud', '/camera/depth_registered/points'),
            ('transform', '/kinect/vrpn_client/estimated_transform'),
            ('voxblox_node/transform', '/kinect/vrpn_client/estimated_transform'),
        ],
        arguments=[
            '--ros-args',
            '--log-level', 'info',
            '-p', 'use_sim_time:=true',
            '-p', 'use_tf_transforms:=false',
            '-p', 'timestamp_tolerance_sec:=0.2',
        ]
    )

    # Static TF: kinect -> camera_rgb_optical_frame (identity)
    static_tf_kinect_to_camera = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_kinect_to_camera_rgb_optical_frame',
        arguments=['0', '0', '0', '0', '0', '0', 'kinect',
                   'camera_rgb_optical_frame'],
        output='screen'
    )

    # Static TF: world -> kinect (identity)
    static_tf_world_to_kinect = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_world_to_kinect',
        arguments=['0', '0', '0', '0', '0', '0', 'world', 'kinect'],
        output='screen'
    )

    return LaunchDescription([
        # Declare arguments first
        play_bag_arg,
        bag_file_arg,
        voxel_size_arg,

        # Launch actions
        static_tf_kinect_to_camera,
        static_tf_world_to_kinect,
        bag_player,
        voxblox_node,
    ])
