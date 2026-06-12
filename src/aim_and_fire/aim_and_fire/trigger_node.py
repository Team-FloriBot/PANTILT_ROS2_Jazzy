#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
import serial


class TriggerNode(Node):

    def __init__(self):
        super().__init__('trigger_node')

        # Parameter für die serielle Schnittstelle konfigurieren
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baud_rate', 9600)

        self.port = self.get_parameter('port').value
        self.baud_rate = self.get_parameter('baud_rate').value

        # Subscriber für das Trigger-Topic
        self.subscription = self.create_subscription(
            Bool,
            '/trigger',
            self.trigger_callback,
            10
        )
        self.get_logger().info(
            f"Trigger-Node gestartet. Lausche auf '/trigger' -> Ausgabe an {self.port}"
        )

    def trigger_callback(self, msg: Bool):
        if msg.data:
            try:
                # Verbindung öffnen, '1' senden und sicher wieder schließen
                with serial.Serial(self.port, self.baud_rate, timeout=1) as ser:
                    ser.write(b'1')
                self.get_logger().info('Ziel erreicht! HIGH Signal (1) an Mikrocontroller gesendet.')
            except serial.SerialException as e:
                self.get_logger().error(f'Fehler bei der seriellen Kommunikation: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = TriggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
