FROM ros:jazzy-ros-base

SHELL ["/bin/bash", "-c"]

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    git \
    libusb-1.0-0 \
    udev \
    && rm -rf /var/lib/apt/lists/*

# Workspace
WORKDIR /ros2_ws

# Code kopieren
COPY src ./src

# Build (Driver + dein Node)
RUN source /opt/ros/jazzy/setup.bash && \
    colcon build

# ROS sourcen
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

# Default: beide starten
CMD ["bash", "-c", "source /opt/ros/jazzy/setup.bash && source /ros2_ws/install/setup.bash && ros2 launch aim_and_fire aim_and_fire.launch.py"]
