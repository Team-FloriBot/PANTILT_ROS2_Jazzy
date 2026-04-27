from setuptools import setup

package_name = 'aim_and_fire'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/aim_and_fire.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your@email.com',
    description='PTU aiming and firing node',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'aim_and_fire = aim_and_fire.aim_and_fire_node:main',
        ],
    },
)
