from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # --- Aim and Fire Node --- 
        Node(
            package='aim_and_fire',
            executable='aim_and_fire',
            name='aim_and_fire',
            output='screen',
            parameters=[
                {'tolerance_deg': 0.3},
                {'offset_z': 0.545},
                {'tilt_offset_deg': 14.26}, #Ausgleich des Neigungswinkels wegen Verschiebung der Nullstellung
                {'tool_offset_z': 0.045},
                {'speed_deg_s': 13.0}, # Begrenzte Geschwindigkeit wegen Spritzpistole
                {'water_speed_m_s': 11.8} # Geschwindigkeit des Wasserstrahls
            ]
        ),
        # --- Trigger Node ---
        Node(
            package='aim_and_fire',
            executable='trigger_node',
            name='trigger_node',
            output='screen',
            parameters=[
                {'port': '/dev/ttyACM0'}, # Hier den Port des XIAO anpassen, falls nötig
                {'baud_rate': 9600}
            ]
        )
    ])
