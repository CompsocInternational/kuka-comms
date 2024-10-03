import kuka_comm_lib


def main():
    print("test program: SYNC reader")
    robot = kuka_comm_lib.KukaRobot(input("Robot Hostname: "))
    try:
        robot.connect()
    except OSError as e:
        print("Failed to connect to robot, ", e.strerror)
        raise e

    try:
        while True:
            axis = robot.get_current_axis()
            pos = robot.get_current_position()
            print(f"Axis: {axis}")
            print(f"Position: {pos}")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
