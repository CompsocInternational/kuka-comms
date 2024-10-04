import kuka_comm_lib
import asyncio


def main():
    print("test program: side to side writer")
    robot = kuka_comm_lib.KukaRobot(input("Robot Hostname: "))
    try:
        robot.connect()
    except OSError as e:
        print("Failed to connect to robot, ", e.strerror)
        raise e
    robot.set_speed(1)

    try:
        while True:
            axis = robot.get_current_axis()
            pos = robot.get_current_position()
            print(f"Axis: {axis}")
            print(f"Position: {pos}")
            
            robot.move_relative(x_rel=200)
            robot.wait_until_ready_to_move()
            robot.move_relative(x_rel=-200)
            robot.wait_until_ready_to_move()
            
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
