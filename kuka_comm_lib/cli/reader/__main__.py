import kuka_comm_lib
import asyncio


async def main():
    print("test program: ASYNC reader")
    robot = kuka_comm_lib.KukaRobot(input("Robot Hostname: "))
    try:
        await robot.connect_async()
    except OSError as e:
        print("Failed to connect to robot, ", e.strerror)
        raise e

    try:
        while True:
            axis = await robot.get_current_axis_async()
            pos = await robot.get_current_position_async()
            print(f"Axis: {axis}")
            print(f"Position: {pos}")
            await asyncio.sleep(0.5)
    finally:
        robot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
