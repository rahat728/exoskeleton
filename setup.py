from setuptools import find_packages, setup
import glob
import os

package_name = 'exoskeleton'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob(os.path.join('launch', '*launch*.py'))),
        ('share/' + package_name + '/scripts', glob.glob(os.path.join('scripts', '*.py'))),
        ('share/' + package_name + '/urdf', glob.glob(os.path.join('urdf', '*.urdf*'))),
        ('share/' + package_name + '/meshes', glob.glob(os.path.join('meshes', '**', '*.STL'), recursive=True)),
        ('share/' + package_name + '/rviz', glob.glob(os.path.join('rviz', '*.rviz'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='rahat',
    maintainer_email='rahat@example.com',
    description='Exoskeleton hand',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
    scripts=[
        'scripts/esp32_hand_bridge.py',
    ],
)
