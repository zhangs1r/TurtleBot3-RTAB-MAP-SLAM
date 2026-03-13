from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    """
    生成 TurtleBot3 RTAB-MAP SLAM 总启动描述文件。
    
    该函数作为顶层启动文件，负责按需启动传感器驱动和 RTAB-MAP 建图程序。
    可以通过 `use_sensors` 参数控制是否启动传感器。
    
    Returns:
        LaunchDescription: 包含所有子启动文件的总启动描述。
    """
    
    use_sensors = LaunchConfiguration('use_sensors', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    use_rtabmap_viz = LaunchConfiguration('use_rtabmap_viz', default='true')
    
    declare_use_sensors = DeclareLaunchArgument(
        'use_sensors',
        default_value='true',
        description='是否启动传感器（激光雷达和摄像头）'
    )
    
    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='是否启动 RViz'
    )

    declare_use_rtabmap_viz = DeclareLaunchArgument(
        'use_rtabmap_viz',
        default_value='true',
        description='是否启动 rtabmap_viz (3D 点云可视化界面)'
    )
    
    # 包含 TurtleBot3 Bringup 启动文件 (OpenCR 驱动和 URDF)
    bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_RTABSLAM'),
                'launch',
                'bringup.launch.py'
            ])
        ])
    )
    
    # 包含传感器启动文件
    sensors_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_RTABSLAM'),
                'launch',
                'sensors.launch.py'
            ])
        ]),
        condition=IfCondition(use_sensors)
    )
    
    # 包含 RTAB-MAP 启动文件
    rtabmap_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_RTABSLAM'),
                'launch',
                'rtabmap.launch.py'
            ])
        ])
    )
    
    # RViz 配置
    rviz_config_dir = PathJoinSubstitution([
        FindPackageShare('turtlebot3_RTABSLAM'),
        'config',
        'turtlebot3_rtabslam.rviz'
    ])

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        condition=IfCondition(use_rviz),
        output='screen'
    )

    rtabmap_viz_node = Node(
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        namespace='rtabmap',
        output='screen',
        condition=IfCondition(use_rtabmap_viz),
        parameters=[{
            'subscribe_depth': True,
            'subscribe_scan': True,
            'frame_id': 'base_footprint',
            'odom_frame_id': 'odom',
            'map_frame_id': 'map',
        }],
        remappings=[
            ('rgb/image', '/camera/color/image_raw'),
            ('rgb/camera_info', '/camera/color/camera_info'),
            ('depth/image', '/camera/aligned_depth_to_color/image_raw'),
            ('scan', '/scan'),
            ('odom', '/odom'),
        ],
    )

    return LaunchDescription([
        declare_use_sensors,
        declare_use_rviz,
        declare_use_rtabmap_viz,
        bringup_launch,
        sensors_launch,
        rtabmap_launch,
        rtabmap_viz_node,
        rviz_node
    ])
