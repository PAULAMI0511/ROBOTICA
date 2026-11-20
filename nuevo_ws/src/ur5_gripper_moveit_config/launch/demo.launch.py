import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_dir = get_package_share_directory('ur5_gripper_moveit_config')
    config_dir = os.path.join(pkg_dir, 'config')

    # Rutas fijas a los archivos de configuración generados por MoveIt Setup Assistant
    urdf_path = os.path.join(config_dir, 'ur5_gripper.urdf.xacro') # O tu archivo urdf/xacro principal
    srdf_path = os.path.join(config_dir, 'ur5_gripper.srdf')
    rviz_path = os.path.join(config_dir, 'moveit.rviz')

    # Nodo Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen'
    )

    # Nodo RViz con la configuración de MoveIt
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_path] if os.path.exists(rviz_path) else []
    )

    return LaunchDescription([
        robot_state_publisher,
        rviz_node
    ])