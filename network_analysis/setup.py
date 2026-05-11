from setuptools import setup
import os
from glob import glob

package_name = 'ghoststack_network'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Researcher',
    maintainer_email='ghoststack@example.com',
    description='GhostStack Network Analysis and Spoofing Module',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'spoofer = ghoststack_network.spoofing_node:main',
            'mavlink_sniff = ghoststack_network.mavlink_sniff:main'
        ],
    },
)
