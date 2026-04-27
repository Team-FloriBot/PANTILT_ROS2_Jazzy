services:
  pantilt:
    build:
      context: .
      dockerfile: Dockerfile

    container_name: pantilt_ros2_jazzy
    network_mode: host
    ipc: host
    privileged: true

    volumes:
      - ./src:/ros2_ws/src
      - /dev:/dev

    environment:
      - ROS_DOMAIN_ID=0

    stdin_open: true
    tty: true

    command: >
      bash -c "source /opt/ros/jazzy/setup.bash &&
               source /ros2_ws/install/setup.bash &&
               ros2 launch aim_and_fire aim_and_fire.launch.py"
