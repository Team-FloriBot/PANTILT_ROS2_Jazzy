#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Point
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool


class AimAndFireNode(Node):

    def __init__(self):
        super().__init__('aim_and_fire')

        # Parameter
        self.declare_parameter('offset_x', 0.0)
        self.declare_parameter('offset_y', 0.0)
        self.declare_parameter('offset_z', 0.545) #Höhe vom Boden zur Neigungsachse

        self.declare_parameter('pan_joint', 'ptu_pan')
        self.declare_parameter('tilt_joint', 'ptu_tilt')

        self.declare_parameter('tolerance_deg', 0.3)
        self.declare_parameter('tilt_offset_deg', 14.26)
        
        self.declare_parameter('speed_deg_s', 13.0) # 15 Grad pro Sekunde als  Startwert 
        self.declare_parameter('water_speed_m_s', 11.8) # Geschwindigkeit des Wasserstrahls

        self.offset_x = self.get_parameter('offset_x').value
        self.offset_y = self.get_parameter('offset_y').value
        self.offset_z = self.get_parameter('offset_z').value

        self.pan_joint = self.get_parameter('pan_joint').value
        self.tilt_joint = self.get_parameter('tilt_joint').value

        self.tolerance = math.radians(
            self.get_parameter('tolerance_deg').value
        )
        
        # physischer Düsenversatz
        self.declare_parameter('tool_offset_z', 0.045) # 45mm Versatz nach oben
        self.tool_offset_z = self.get_parameter('tool_offset_z').value
        
        # Umrechnung des Offsets in Radiant
        self.tilt_offset = math.radians(
            self.get_parameter('tilt_offset_deg').value
        )

        # Zustand
        self.target_pan = None
        self.target_tilt = None
        self.has_fired = False

        # Publisher
        self.cmd_pub = self.create_publisher(
            JointState, '/ptu/cmd', 10)

        self.trigger_pub = self.create_publisher(
            Bool, '/trigger', 10)

        # Subscriber
        self.create_subscription(
            Point, '/target_point', self.target_callback, 10)

        self.create_subscription(
            JointState, '/ptu/state', self.state_callback, 10)

    def target_callback(self, msg: Point):
        # Aktuelle Wunschgeschwindigkeit live auslesen und in Radiant umrechnen
        speed_rad_s = math.radians(self.get_parameter('speed_deg_s').value)
        
        # Koordinaten relativ zur PTU-Achse berechnen
        x = -(msg.x - self.offset_x)
        y = msg.y - self.offset_y
        z = msg.z - self.offset_z
        
        # Horizontale Distanz und direkte Sichtlinie (Hypotenuse) zum Ziel
        horizontal = math.hypot(x, y)
        R = math.hypot(horizontal, z) # Absolute Distanz von Achse zu Ziel

        # Sicherheitsabfrage: Ziel muss weiter weg sein als Düsenversatz
        if R > self.tool_offset_z:
            # Winkel zum Ziel aus Sicht der Rotationsachse
            beta = math.atan2(z, horizontal)
            
            # Korrekturwinkel für den Parallaxenfehler (Düse sitzt höher, also muss PTU weiter nach unten zielen)
            alpha = math.asin(self.tool_offset_z / R)
            
            # Ballistische Kompensation 
            v_water = self.get_parameter('water_speed_m_s').value
            g = 9.81 # Erdbeschleunigung in m/s2 
            
            # Flugzeit t = Distanz / Geschwindigkeit
            t = R / v_water
            
            # Fallstrecke des Wassers in Metern (freier Fall)
            drop = 0.5 * g * (t ** 2)
            
            # Notwendiger Winkel nach oben, um den Fall auszugleichen
            drop_angle = math.atan2(drop, R)
            
            # Gesamtwinkel = Basiswinkel - Parallaxenkorrektur + Getriebekorrektur + Ballistik
            tilt = beta - alpha + self.tilt_offset + drop_angle
            pan = math.atan2(x, y)
        else:
            self.get_logger().warn("Ziel ist zu nah an der PTU!")
            return

        self.target_pan = pan
        self.target_tilt = tilt
        self.has_fired = False
        
        # Befehl an PTU senden
        cmd = JointState()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.name = [self.pan_joint, self.tilt_joint]
        cmd.position = [pan, tilt]
        cmd.velocity = [speed_rad_s, speed_rad_s] # Geschwindigkeit für beide Achsen an Treiber

        self.cmd_pub.publish(cmd)

        self.get_logger().info(
            f'Ziel empfangen → pan={math.degrees(pan):.2f}°, '
            f'tilt={math.degrees(tilt):.2f}° (inkl. Offset)'
        )

    def state_callback(self, msg: JointState):
        if self.target_pan is None:
            return

        if self.has_fired:
            return

        try:
            pan_idx = msg.name.index(self.pan_joint)
            tilt_idx = msg.name.index(self.tilt_joint)
        except ValueError:
            return

        pan_error = abs(msg.position[pan_idx] - self.target_pan)
        tilt_error = abs(msg.position[tilt_idx] - self.target_tilt)

        if pan_error < self.tolerance and tilt_error < self.tolerance:
            self.fire()

    def fire(self):
        trig = Bool()
        trig.data = True
        self.trigger_pub.publish(trig)

        self.has_fired = True

        self.get_logger().info('Ziel erreicht → Schuss ausgelöst')


def main():
    rclpy.init()
    node = AimAndFireNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
