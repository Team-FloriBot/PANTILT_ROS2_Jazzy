FROM ros:jazzy-ros-base

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-pip \
    git \
    libusb-1.0-0 \
    udev \
    python3-serial \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws

# Eigenes Paket kopieren
COPY src ./src

# ROS-2-PTU-Treiber holen
RUN git clone https://github.com/vicoslab/flir_ptu_driver.git src/flir_ptu_driver

# Workspace bauen
RUN source /opt/ros/jazzy/setup.bash && \
    colcon build

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc && \
    echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]
