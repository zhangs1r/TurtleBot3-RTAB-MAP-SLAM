#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import ThisLaunchFileDir
from launch_ros.actions import Node

def generate_launch_description():
    """
    生成 TurtleBot3 Burger 的自定义启动文件。
    
    这个启动文件基于官方的 robot.launch.py，但移除了激光雷达的启动部分，
    因为激光雷达已经由 sensors.launch.py 独立管理。
    
    主要功能：
    1. 启动 turtlebot3_state_publisher (加载 URDF 模型)
    2. 启动 turtlebot3_node (OpenCR 驱动，处理里程计和电机控制)
    """

    # 获取 TURTLEBOT3_MODEL 环境变量，默认为 burger
    TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'burger')
    
    usb_port = LaunchConfiguration('usb_port', default='/dev/ttyACM0')
    
    # 定义参数文件路径
    tb3_param_dir = LaunchConfiguration(
        'tb3_param_dir',
        default=os.path.join(
            get_package_share_directory('turtlebot3_bringup'),
            'param',
            TURTLEBOT3_MODEL + '.yaml'))

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    namespace = LaunchConfiguration('namespace', default='')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='如果为 true，则使用仿真 (Gazebo) 时钟'),
            
        DeclareLaunchArgument(
            'namespace',
            default_value=namespace,
            description='节点命名空间'),

        DeclareLaunchArgument(
            'usb_port',
            default_value=usb_port,
            description='连接 OpenCR 的 USB 端口'),

        DeclareLaunchArgument(
            'tb3_param_dir',
            default_value=tb3_param_dir,
            description='要加载的 turtlebot3 参数文件的完整路径'),

        # 包含 turtlebot3_state_publisher.launch.py
        # 这会发布 robot_description 和 TF 变换
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('turtlebot3_bringup'), 'launch', 'turtlebot3_state_publisher.launch.py')
            ),
            launch_arguments={'use_sim_time': use_sim_time, 'namespace': namespace}.items(),
        ),

        # 启动 turtlebot3_node (OpenCR 驱动)
        Node(
            package='turtlebot3_node',
            executable='turtlebot3_ros',
            parameters=[tb3_param_dir, {'namespace': namespace}],
            arguments=['-i', usb_port],
            remappings=[('/cmd_vel', '/cmd_vel')], # 确保话题名称正确
            output='screen'),
            
        # 启动 Twist 转 TwistStamped 节点 (兼容旧版 teleop)
        Node(
            package='turtlebot3_RTABSLAM',
            executable='twist_to_twist_stamped.py',
            name='twist_converter',
            remappings=[
                ('/cmd_vel_in', '/cmd_vel_twist'), # 键盘发送到这里
                ('/cmd_vel_out', '/cmd_vel')       # 转换后发给底盘
            ],
            output='screen'
        ),
    ])
