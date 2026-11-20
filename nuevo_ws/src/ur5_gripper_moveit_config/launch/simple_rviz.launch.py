import os
import glob
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_dir = get_package_share_directory('ur5_gripper_moveit_config')
    config_dir = os.path.join(pkg_dir, 'config')

    # Buscar y procesar correctamente el archivo .xacro
    xacro_files = glob.glob(os.path.join(config_dir, '*.xacro'))
    if xacro_files:
        doc = xacro.process_file(xacro_files[0])
        robot_description_config = doc.toxml()
    else:
        robot_description_config = ""

    # Cargar SRDF si existe
    srdf_files = glob.glob(os.path.join(config_dir, '*.srdf'))
    robot_description_semantic_config = ""
    if srdf_files:
        with open(srdf_files[0], 'r') as f:
            robot_description_semantic_config = f.read()

    rviz_config_path = os.path.join(config_dir, 'moveit.rviz')

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description_config}]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_path] if os.path.exists(rviz_config_path) else [],
            parameters=[
                {'robot_description': robot_description_config},
                {'robot_description_semantic': robot_description_semantic_config}
            ]
        )
    ])