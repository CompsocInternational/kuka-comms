import kuka_comm_lib, asyncio


async def main():
    print("test program: ASYNC reader")
    robot = kuka_comm_lib.KukaRobot(input("Robot Hostname: "))
    try:
        await robot.connect_async()
    except:
        print("Failed to connect to robot")
        return

    try:
        while True:
            axis = await robot.get_current_axis_async()
            pos = await robot.get_current_position_async()
            print(f"Axis: {axis}")
            print(f"Position: {pos}")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
