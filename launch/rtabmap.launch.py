from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """
    生成 RTAB-MAP SLAM 启动描述文件。
    
    该版本强制使用 'rtabmap' 命名空间以匹配 RVIZ 默认配置话题 (/rtabmap/cloud_map)。
    同时优化了同步参数和坐标系配置。
    """
    
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # 核心参数配置
    parameters = {
        'use_sim_time': use_sim_time,
        'subscribe_depth': True,
        'subscribe_scan': True,
        'frame_id': 'base_footprint',
        'odom_frame_id': 'odom',
        'map_frame_id': 'map',
        
        # 极致同步参数优化
        'approx_sync': True,
        'queue_size': 500,             # 大幅增加队列
        'approx_sync_max_interval': 0.5, # 放宽同步间隔容差 (秒)
        
        # 注册策略：视觉 + 激光融合
        'Reg/Strategy': '2',
        'Reg/Force3DoF': 'true',
        
        # 地图生成控制
        'Grid/Sensor': '0',            # 2D 地图使用激光雷达 (保持整洁)
        'Grid/FromDepth': 'false',
        'Grid/RangeMax': '10.0',
        
        # 3D 可视化控制
        'Rtabmap/PublishMapData': 'true',
        'Rtabmap/DetectionRate': '2.0', # 提高检测率以更快生成初始地图
        'RGBD/LinearUpdate': '0.01',   # 减小更新阈值，更容易触发建图
        'RGBD/AngularUpdate': '0.01',
        'Mem/IncrementalMemory': 'true',
        
        # QoS (匹配 RealSense 默认 Reliable 模式)
        'qos_image': 1,
        'qos_depth': 1,
        'qos_camera_info': 1,
        'qos_scan': 1,
        'qos_odom': 1,
    }

    # 话题重映射 (显式使用绝对路径)
    remappings = [
        ('rgb/image', '/camera/color/image_raw'),
        ('rgb/camera_info', '/camera/color/camera_info'),
        ('depth/image', '/camera/aligned_depth_to_color/image_raw'),
        ('scan', '/scan'),
        ('odom', '/odom'),
    ]

    # 将节点放在 'rtabmap' 命名空间中
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        
        name='rtabmap',
        namespace='rtabmap',
        output='screen',
        parameters=[parameters],
        remappings=remappings,
        arguments=['--delete_db_on_start']
    )

    map_assembler_node = Node(
        package='rtabmap_util',
        executable='map_assembler',
        name='map_assembler',
        namespace='rtabmap',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        rtabmap_node,
        map_assembler_node
    ])
