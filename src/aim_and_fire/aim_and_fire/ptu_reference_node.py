#!/usr/bin/env python3

import os
import threading

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class PtuReferenceNode(Node):
    def __init__(self) -> None:
        super().__init__("ptu_reference_node")

        self.declare_parameter(
            "port",
            os.environ.get("PTU_PORT", "/dev/ttyUSB0"),
        )

        self._serial_lock = threading.Lock()

        self._service = self.create_service(
            Trigger,
            "/ptu/reference",
            self.reference_callback,
        )

        self.get_logger().info(
            "PTU-Referenz-Service ist unter /ptu/reference verfügbar"
        )

    def reference_callback(
        self,
        request: Trigger.Request,
        response: Trigger.Response,
    ) -> Trigger.Response:
        del request

        port = str(self.get_parameter("port").value)

        try:
            if not os.path.exists(port):
                raise FileNotFoundError(f"PTU-Port {port} existiert nicht")

            with self._serial_lock:
                with open(port, "wb", buffering=0) as serial_port:
                    serial_port.write(b"R\r")

            response.success = True
            response.message = (
                f"PTU-Referenzfahrt über {port} ausgelöst."
            )

        except Exception as exc:
            response.success = False
            response.message = (
                f"PTU-Referenzfahrt fehlgeschlagen: {exc}"
            )

        return response


def main(args=None) -> None:
    rclpy.init(args=args)

    node = PtuReferenceNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
