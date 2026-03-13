# TurtleBot3 RTAB-MAP SLAM

## 📌 项目简介
本项目（`turtlebot3_RTABSLAM`）是面向 TurtleBot3 Burger 的 RTAB-Map（ROS 2 Humble）建图配置，组合使用：
- **RPLIDAR A2M12**：提供 2D 激光用于生成占据栅格与约束位姿
- **Intel RealSense D435i**：提供 RGB-D 用于生成彩色 3D 点云地图与回环检测

默认策略是“2D 导航友好 + 3D 可视化/建模”：2D `/rtabmap/map` 用于导航链路，3D 点云通过 `/rtabmap/cloud_map` 展示与导出 🧭

## 🚀 硬件配置
- **机器人底盘**: TurtleBot3 Burger (OpenCR)
- **激光雷达**: RPLIDAR A2M12 (串口: `/dev/ttyUSB0`, 波特率: 256000)
- **深度相机**: Intel RealSense D435i (USB 3.0)

## 🛠️ 安装与编译

1. **安装依赖**
   ```bash
   sudo apt install ros-humble-rtabmap-ros ros-humble-realsense2-camera ros-humble-rplidar-ros
   ```

2. **编译工作空间**
   ```bash
   cd ~/turtlebot3_ws
   colcon build --packages-select turtlebot3_RTABSLAM
   source install/setup.bash
   ```

## 🏁 启动步骤

### 1) 启动 SLAM 建图（终端 1）
此命令会同时启动（可通过参数开关控制）：
- 机器人底盘驱动 (OpenCR)
- RPLIDAR A2M12 驱动
- RealSense D435i 驱动
- RTAB-MAP 建图算法
- rtabmap_viz（可选，推荐：效果最接近“彩色 3D 点云建图”界面）
- RViz2（可选）
- 速度指令转换器 (Twist -> TwistStamped)

```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_RTABSLAM turtlebot3_rtabslam.launch.py
```

常用启动参数：
- `use_sensors:=true|false`：是否启动雷达/相机驱动
- `use_rtabmap_viz:=true|false`：是否启动 rtabmap_viz
- `use_rviz:=true|false`：是否启动 RViz2

示例（只开 rtabmap_viz，不开 RViz2）：
```bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_RTABSLAM turtlebot3_rtabslam.launch.py use_rviz:=false use_rtabmap_viz:=true
```

### 2) 启动键盘控制（终端 2）
由于我们已经集成了速度指令转换器，您可以直接使用标准的键盘控制节点，但需要进行话题重映射，将其输出指向转换器的输入端口 `/cmd_vel_twist`：

```bash
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard --ros-args -r /cmd_vel:=/cmd_vel_twist
```

现在，您可以使用键盘控制机器人移动，并在 RViz 中实时查看建图效果！

## 🧩 主要话题（快速自检）
- 2D 激光：`/scan`
- 里程计：`/odom`
- 2D 占据栅格：`/rtabmap/map`（注意：不是 `/map`）
- 3D 彩色点云地图：`/rtabmap/cloud_map`

## 💡 遇到的困难与解决方案 (经验总结)

### 1. 机器人无法移动
*   **现象**: 键盘控制节点运行正常，但机器人纹丝不动。
*   **原因**: TurtleBot3 Burger 的底盘固件开启了 `enable_stamped_cmd_vel`，只接受带有时间戳的 `geometry_msgs/TwistStamped` 消息，而键盘节点发送的是普通的 `Twist` 消息。
*   **解决**: 编写了一个转换节点 `scripts/twist_to_twist_stamped.py`，将 `Twist` 转换为 `TwistStamped` 并转发给底盘。

### 2. RViz 报错 "Frame [map] does not exist"
*   **现象**: 激光雷达数据正常，但无法建立地图，TF 树断裂。
*   **原因**: RTAB-MAP 没有接收到有效的传感器数据，导致无法初始化和发布 `map` -> `odom` 的 TF 变换。具体原因是 RealSense 话题名称默认为 `/camera/camera/...`，而 RTAB-MAP 默认订阅 `/camera/...`。
*   **解决**: 在 `rtabmap.launch.py` 中修正了所有相机话题的订阅路径，使其与 RealSense 驱动的输出一致。

### 3. RealSense 图像不显示或卡顿
*   **现象**: `/camera/camera/color/image_raw` 话题频率为 0 或极低。
*   **原因**: 树莓派/上位机 USB 带宽不足，无法承载默认的 1280x720 @ 30fps 数据流。
*   **解决**: 在 `sensors.launch.py` 中将 RGB 和深度流的分辨率降低至 **640x480**，帧率降低至 **15fps**。

### 4. `/map` 没有发布者（Publisher count: 0）
*   **现象**: `ros2 topic info /map` 显示 Publisher 为 0。
*   **原因**: 本项目将 RTAB-Map 节点放在 `rtabmap` 命名空间中，地图默认发布到 `/rtabmap/map`。
*   **解决**: 将 RViz 的 Map 订阅改为 `/rtabmap/map` 与 `/rtabmap/map_updates`，或直接订阅 `/rtabmap/map` 查看。

### 5. 建图效果漂移
*   **解决**: 在 `rtabmap.launch.py` 中增加了以下参数优化：
    *   `Reg/Strategy=2`：使用视觉+激光融合策略（更稳）
    *   `Reg/Force3DoF=true`：强制平面运动约束
    *   `Grid/RangeMax=10.0`：限制建图距离，减少远处噪声

### 6. 3D 点云地图 `/rtabmap/cloud_map` 没有输出
*   **现象**: RViz/rtabmap_viz 看不到完整 3D 点云，或 `ros2 topic info /rtabmap/cloud_map` Publisher 为 0。
*   **原因**: 3D 全局点云需要由 `rtabmap_util/map_assembler` 订阅 `mapData` 进行组装发布。
*   **解决**:
    1) 确认已启动 `map_assembler`（本项目已默认启动）
    2) 检查 `ros2 topic info /rtabmap/mapData` 与 `/rtabmap/cloud_map`
    3) 若日志目录只读导致节点异常退出，可临时设置：`export ROS_LOG_DIR=/tmp/roslog`
