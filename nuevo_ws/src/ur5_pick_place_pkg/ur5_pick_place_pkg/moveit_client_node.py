import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MotionPlanRequest, PlanningOptions

ARM_JOINTS = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
              'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
GRIPPER_JOINTS = ['gripper_finger_joint', 'right_finger_joint']

READY = [0.0, -1.2, 1.2, -1.57, -1.57, 0.0]
TARGET = [0.5, -1.2, 1.4, -1.57, -1.57, 0.5]
HOME = [0.0, -1.57, 1.57, -1.57, -1.57, 0.0]


class MoveItClient(Node):
    def __init__(self):
        super().__init__('moveit_client_node')
        self.client = ActionClient(self, MoveGroup, '/move_action')

    def go(self, group, names, values, execute=True):
        goal = MoveGroup.Goal()
        req = MotionPlanRequest()
        req.group_name = group
        req.pipeline_id = 'ompl'
        req.num_planning_attempts = 5
        req.allowed_planning_time = 5.0
        req.max_velocity_scaling_factor = 0.3
        req.max_acceleration_scaling_factor = 0.3
        c = Constraints()
        for n, v in zip(names, values):
            c.joint_constraints.append(JointConstraint(
                joint_name=n, position=float(v),
                tolerance_above=0.005, tolerance_below=0.005, weight=1.0))
        req.goal_constraints.append(c)
        goal.request = req
        goal.planning_options = PlanningOptions(plan_only=not execute)
        modo = 'plan+ejecucion' if execute else 'solo plan'
        self.get_logger().info(f'[{group}] {modo} -> {values}')
        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('move_group no disponible (/move_action)')
            return False
        send = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send)
        handle = send.result()
        if not handle.accepted:
            self.get_logger().error('Objetivo rechazado')
            return False
        res = handle.get_result_async()
        rclpy.spin_until_future_complete(self, res)
        code = res.result().result.error_code.val
        self.get_logger().info(f'Resultado error_code={code} ({"OK" if code == 1 else "FALLO"})')
        return code == 1


def main(args=None):
    rclpy.init(args=args)
    n = MoveItClient()
    try:
        n.go('ur_arm', ARM_JOINTS, READY)
        n.go('gripper', GRIPPER_JOINTS, [0.04, 0.04], execute=False)
        n.go('ur_arm', ARM_JOINTS, TARGET)
        n.go('gripper', GRIPPER_JOINTS, [0.004, 0.004], execute=False)
        n.go('ur_arm', ARM_JOINTS, HOME)
    except KeyboardInterrupt:
        pass
    n.destroy_node()
    rclpy.try_shutdown()
