#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TwistToTwistStamped(Node):
    def __init__(self):
        super().__init__('twist_to_twist_stamped')
        
        # 订阅 /cmd_vel_in (Twist)
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel_in',
            self.listener_callback,
            10)
            
        # 发布 /cmd_vel_out (TwistStamped)
        self.publisher = self.create_publisher(
            TwistStamped,
            '/cmd_vel_out',
            10)
            
        self.get_logger().info('Twist to TwistStamped converter started.')

    def listener_callback(self, msg):
        stamped_msg = TwistStamped()
        stamped_msg.header.stamp = self.get_clock().now().to_msg()
        stamped_msg.header.frame_id = 'base_link'
        stamped_msg.twist = msg
        
        self.publisher.publish(stamped_msg)

def main(args=None):
    rclpy.init(args=args)
    converter = TwistToTwistStamped()
    rclpy.spin(converter)
    converter.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
