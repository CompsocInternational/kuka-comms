import asyncio
from typing import Optional

from kuka_comm_lib.positions import AxisPos
from kuka_comm_lib.connection import RobotConnection
from kuka_comm_lib.exceptions import RobotAlreadyMovingError
from kuka_comm_lib.positions import CartesianPos


class KukaRobot:
    _connection: RobotConnection
    # This is used to ensure any other parts of the program can not inturrupt methods that should run as if they are sync.
    # _blocking_loop: asyncio.AbstractEventLoop

    def __init__(self, host: str, port: int = 7000) -> None:
        self._connection = RobotConnection(host, port)
        # self._blocking_loop = asyncio.new_event_loop()
        pass

    def move_relative(
        self,
        x_rel: float,
        y_rel: float,
        z_rel: float,
        wait_until_complete: bool = False,
    ):
        asyncio.run(
            self.move_relative_async(
                x_rel, y_rel, z_rel, wait_until_complete=wait_until_complete
            )
        )

    async def move_relative_async(
        self,
        x_rel: float,
        y_rel: float,
        z_rel: float,
        wait_until_complete: bool = False,
    ):
        """
        move to cartesian coordinates, relative to the current position
        """

        x, y, z, a, b, c = await self.get_current_position_async()
        new_x = x + x_rel
        new_y = y + y_rel
        new_z = z + z_rel

        target = CartesianPos(new_x, new_y, new_z, a, b, c)

        await self._goto(target, wait_until_complete=wait_until_complete)

    def goto(
        self,
        x: Optional[float],
        y: Optional[float],
        z: Optional[float],
        a: Optional[float],
        b: Optional[float],
        c: Optional[float],
        wait_until_complete: bool = False,
    ):
        asyncio.run(
            self.goto_async(x, y, z, a, b, c, wait_until_complete=wait_until_complete)
        )

    async def goto_async(
        self,
        x: Optional[float],
        y: Optional[float],
        z: Optional[float],
        a: Optional[float],
        b: Optional[float],
        c: Optional[float],
        wait_until_complete: bool = False,
    ):
        """
        move to cartesian coordinates, relative to the set base (bottom left of conveyor)
        """

        current = await self.get_current_position_async()

        target = CartesianPos(
            x or current.x,
            y or current.y,
            z or current.z,
            a or current.a,
            b or current.b,
            c or current.c,
        )
        await self._goto(target, wait_until_complete=wait_until_complete)

        pass

    def get_current_position(self) -> CartesianPos:
        return asyncio.run(self.get_current_position_async())

    async def get_current_position_async(self) -> CartesianPos:
        """
        get the current position of the robot
        """
        # {E6POS: X 1991.282, Y 91.03918, Z 1659.515, A 160.2559, B 63.59148, C 161.3706, S 2, T 35, E1 0.0, E2 0.0, E3 0.0, E4 0.0, E5 0.0, E6 0.0}
        pos_string = await self._connection.get_variable("POS_ACT")
        pos_list = pos_string.removeprefix("{E6POS: ").removesuffix("}").split(", ")
        x, y, z, a, b, c = None, None, None, None, None, None
        for pos in pos_list:
            key, value = pos.split(" ")
            key = key.strip()
            value = value.strip()
            if key == "X":
                x = float(value)
            elif key == "Y":
                y = float(value)
            elif key == "Z":
                z = float(value)
            elif key == "A":
                a = float(value)
            elif key == "B":
                b = float(value)
            elif key == "C":
                c = float(value)
        if x is None or y is None or z is None or a is None or b is None or c is None:
            raise ValueError(f'Invalid position string: "{pos_string}"')
        return CartesianPos(x, y, z, a, b, c)

    def get_current_axis(self) -> AxisPos:
        return asyncio.run(self.get_current_axis_async())

    async def get_current_axis_async(self) -> AxisPos:
        """
        get the current position of the robot
        """
        # {E6AXIS: A1 -2.820527, A2 -73.70981, A3 80.95905, A4 5.768665, A5 17.77479, A6 -15.32642, E1 0.0, E2 0.0, E3 0.0, E4 0.0, E5 0.0, E6 0.0}
        pos_string = await self._connection.get_variable("AXIS_ACT")
        pos_list = pos_string.removeprefix("{E6AXIS: ").removesuffix("}").split(", ")
        a1, a2, a3, a4, a5, a6 = None, None, None, None, None, None
        for pos in pos_list:
            key, value = pos.split(" ")
            key = key.strip()
            value = value.strip()
            if key == "A1":
                a1 = float(value)
            elif key == "A2":
                a2 = float(value)
            elif key == "A3":
                a3 = float(value)
            elif key == "A4":
                a4 = float(value)
            elif key == "A5":
                a5 = float(value)
            elif key == "A6":
                a6 = float(value)
        if (
            a1 is None
            or a2 is None
            or a3 is None
            or a4 is None
            or a5 is None
            or a6 is None
        ):
            raise ValueError(f'Invalid position string: "{pos_string}"')
        return AxisPos(a1, a2, a3, a4, a5, a6)

    async def _goto(self, target: CartesianPos, wait_until_complete: bool = False):
        """
        *internal*
        move to cartesian coordinates
        """
        if not await self.is_ready_to_move_async():
            raise RobotAlreadyMovingError("Robot is already moving")

        pos_value_string = f"{{POS: X {target.x}, Y {target.y}, Z {target.z}, A {target.a}, B {target.b}, C {target.c}}}"
        await self._connection.set_variable("RUN_FRAME", pos_value_string)
        if wait_until_complete:
            await self.wait_until_ready_to_move_async()

    def wait_until_ready_to_move(self):
        return asyncio.run(self.wait_until_ready_to_move_async())

    async def wait_until_ready_to_move_async(self):
        while not await self.is_ready_to_move_async():
            await asyncio.sleep(0.1)

    def is_ready_to_move(self) -> bool:
        return asyncio.run(self.is_ready_to_move_async())

    async def is_ready_to_move_async(self) -> bool:
        in_progress = await self._connection.get_variable("MOVE_IN_PROGRESS")
        if in_progress == "0":
            return True
        return False

    def connect(self) -> None:
        asyncio.run(self.connect_async())

    async def connect_async(self) -> None:
        await self._connection.connect()

    def is_connected(self) -> bool:
        return self._connection.is_connected()

    def disconnect(self) -> None:
        asyncio.run(self.disconnect_async())

    async def disconnect_async(self) -> None:
        await self._connection.disconnect()
