from glob import glob
from setuptools import find_packages, setup

package_name = 'devkit_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*')),
        ('share/' + package_name + '/urdf', glob('urdf/*.urdf.xacro')),
        ('share/' + package_name + '/meshes/visual', glob('meshes/visual/*.dae')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mic-732',
    maintainer_email='mic-732@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    entry_points={
        'console_scripts': [],
    },
)
