import time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from builtin_interfaces.msg import Duration
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, String, Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM_JOINTS = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
              'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
OPEN, CLOSED = 0.04, 0.004

LATCHED = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)

# Puntos de interes (rad)
HOME = [0.0, -1.57, 1.57, -1.57, -1.57, 0.0]
PICK = [0.5, -1.2, 1.6, -1.9, -1.57, 0.0]
MID = [0.0, -1.0, 1.2, -1.7, -1.57, 0.0]
PLACE = [-0.6, -1.2, 1.6, -1.9, -1.57, 0.0]

# (nombre, joints, duracion, operaciones)
ROUTINE = [
    ('HOME', HOME, 3.0, [('info', 'Inicio de rutina'), ('gripper', 'open'),
                         ('do', True)]),
    ('PICK', PICK, 3.0, [('info', 'Esperando pieza en /digital_input_1'),
                         ('wait_di', None), ('gripper', 'close')]),
    ('MID', MID, 3.0, [('info', 'Pieza levantada, en transito')]),
    ('PLACE', PLACE, 3.0, [('gripper', 'open'), ('do', False),
                           ('info', 'Pieza depositada')]),
    ('HOME', HOME, 3.0, [('info', 'Rutina finalizada')]),
]


class PickAndPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_place_node')
        self.arm_pub = self.create_publisher(
            JointTrajectory, '/scaled_joint_trajectory_controller/joint_trajectory', 10)
        self.grip_pub = self.create_publisher(Float64MultiArray, '/gripper_controller/commands', 10)
        self.do_pub = self.create_publisher(Bool, '/digital_output_1', LATCHED)
        self.status_pub = self.create_publisher(String, '/robot_status', 10)
        self.di = False
        self.js = {}
        self.create_subscription(Bool, '/digital_input_1', self.on_di, LATCHED)
        self.create_subscription(JointState, '/joint_states', self.on_js, 10)

    def on_di(self, msg):
        self.di = msg.data

    def on_js(self, msg):
        self.js = dict(zip(msg.name, msg.position))

    def spin_for(self, s):
        end = time.time() + s
        while rclpy.ok() and time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def move_arm(self, joints, dur):
        msg = JointTrajectory(joint_names=ARM_JOINTS)
        pt = JointTrajectoryPoint(positions=list(joints))
        pt.time_from_start = Duration(sec=int(dur), nanosec=0)
        msg.points.append(pt)
        self.arm_pub.publish(msg)
        self.spin_for(dur)
        deadline = time.time() + 5.0
        while rclpy.ok() and time.time() < deadline:
            if self.js and all(abs(self.js.get(j, 9e9) - q) < 0.05
                               for j, q in zip(ARM_JOINTS, joints)):
                return
            rclpy.spin_once(self, timeout_sec=0.05)
        self.get_logger().warn('No se alcanzo la tolerancia; se continua')

    def gripper(self, action):
        v = OPEN if action == 'open' else CLOSED
        self.grip_pub.publish(Float64MultiArray(data=[v, v]))
        self.get_logger().info(f'   -> Gripper {action} ({v} m)')
        self.spin_for(1.5)

    def run(self):
        self.spin_for(1.0)
        for i, (name, joints, dur, ops) in enumerate(ROUTINE, 1):
            self.get_logger().info(f'--- Paso {i}/{len(ROUTINE)}: {name} ---')
            self.status_pub.publish(String(data=f'En {name}'))
            self.move_arm(joints, dur)
            for op, arg in ops:
                if op == 'info':
                    self.get_logger().info(f'   -> [INFO] {arg}')
                elif op == 'gripper':
                    self.gripper(arg)
                elif op == 'do':
                    self.do_pub.publish(Bool(data=arg))
                    self.get_logger().info(f'   -> Salida digital 1 = {arg}')
                    self.spin_for(0.3)
                elif op == 'wait_di':
                    while rclpy.ok() and not self.di:
                        rclpy.spin_once(self, timeout_sec=0.1)
                    self.get_logger().info('   -> Entrada digital 1 activa, se continua')
        self.get_logger().info('=== Pick and Place finalizado ===')


def main(args=None):
    rclpy.init(args=args)
    node = PickAndPlaceNode()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
