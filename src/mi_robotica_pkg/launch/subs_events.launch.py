from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo, RegisterEventHandler, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart
from launch_ros.actions import Node
from launch.substitutions import FindExecutable, LaunchConfiguration, PythonExpression

def generate_launch_description():
    turtlesim_ns = LaunchConfiguration('turtlesim_ns')
    use_provided_red = LaunchConfiguration('use_provided_red')
    new_background_r = LaunchConfiguration('new_background_r')

    turtlesim_node = Node(
        package='turtlesim',
        namespace=turtlesim_ns,
        executable='turtlesim_node',
        name='sim'
    )

    # 1. Cambiar parámetro apuntando al nodo exacto (/turtlesim2/sim)
    change_background = ExecuteProcess(
        condition=IfCondition(
            PythonExpression([new_background_r, " == 200 and ", use_provided_red])
        ),
        cmd=[
            FindExecutable(name='ros2'),
            'param', 'set',
            '/turtlesim2/sim',
            'background_r',
            new_background_r
        ],
        shell=True
    )

    # 2. Refrescar la pantalla con /clear
    clear_screen = ExecuteProcess(
        condition=IfCondition(
            PythonExpression([new_background_r, " == 200 and ", use_provided_red])
        ),
        cmd=[
            FindExecutable(name='ros2'),
            'service', 'call',
            '/turtlesim2/clear',
            'std_srvs/srv/Empty'
        ],
        shell=True
    )

    return LaunchDescription([
        DeclareLaunchArgument('turtlesim_ns', default_value='turtlesim1'),
        DeclareLaunchArgument('use_provided_red', default_value='False'),
        DeclareLaunchArgument('new_background_r', default_value='200'),

        turtlesim_node,

        # Esperar 2 segundos tras iniciar turtlesim para cambiar el parámetro y refrescar
        RegisterEventHandler(
            OnProcessStart(
                target_action=turtlesim_node,
                on_start=[
                    LogInfo(msg="Iniciando turtlesim..."),
                    TimerAction(
                        period=2.0,
                        actions=[
                            change_background,
                            clear_screen
                        ]
                    )
                ]
            )
        )
    ])
