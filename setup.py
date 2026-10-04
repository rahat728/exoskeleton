import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'exoskeleton'


def mesh_data_files():
    entries = []
    for root, _, files in os.walk('meshes'):
        if not files:
            continue
        entries.append(
            (
                os.path.join('share', package_name, root),
                [os.path.join(root, name) for name in files],
            )
        )
    return entries


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ] + mesh_data_files(),
    install_requires=['setuptools', 'pyyaml'],
    zip_safe=True,
    maintainer='rahat',
    maintainer_email='rahat@todo.todo',
    description='Hand exoskeleton URDF visualization and ESP32 servo hardware bridge',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'hardware_bridge = exoskeleton.hardware_bridge:main',
        ],
    },
)
