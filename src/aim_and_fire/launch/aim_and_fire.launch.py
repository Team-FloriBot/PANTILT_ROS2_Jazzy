from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='aim_and_fire',
            executable='aim_and_fire',
            name='aim_and_fire',
            output='screen',
            parameters=[
                {'tolerance_deg': 0.3},
                {'offset_z': 0.225}
            ]
        )
    ])
