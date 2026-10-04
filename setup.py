# Copyright 2026 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import find_packages, setup
import glob
import os

package_name = 'exoskeleton'

data_files = [
    ('share/ament_index/resource_index/packages',
     ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
]

launch_files = glob.glob(os.path.join('launch', '*launch*.py'))
if launch_files:
    data_files.append(('share/' + package_name + '/launch', launch_files))

script_files = glob.glob(os.path.join('scripts', '*.py'))
if script_files:
    data_files.append(('share/' + package_name + '/scripts', script_files))

urdf_files = glob.glob(os.path.join('urdf', '*.urdf*'))
if urdf_files:
    data_files.append(('share/' + package_name + '/urdf', urdf_files))

mesh_files = glob.glob(os.path.join('meshes', '**', '*.STL'), recursive=True)
if mesh_files:
    data_files.append(('share/' + package_name + '/meshes', mesh_files))

rviz_files = glob.glob(os.path.join('rviz', '*.rviz'))
if rviz_files:
    data_files.append(('share/' + package_name + '/rviz', rviz_files))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
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
