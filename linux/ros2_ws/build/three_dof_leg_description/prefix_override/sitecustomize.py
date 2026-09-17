import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ben/x/10DOF-DUCK/linux/ros2_ws/install/three_dof_leg_description'
