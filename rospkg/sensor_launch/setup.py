from glob import glob
from setuptools import find_packages, setup

package_name = 'sensor_launch'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data={
        package_name: ['*.so'],
    },
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*'))
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mic-732',
    maintainer_email='mic-732@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [
            'camera = sensor_launch.camera:main',
            'camera_v4l2 = sensor_launch.camera_v4l2:main',
            'camera_resize = sensor_launch.camera_resize:main',
            'image_resize = sensor_launch.image_resize:main',
            'pointcloud_downsample = sensor_launch.pointcloud_downsample:main',
        ],
    },
)
