import asyncio
import time
from typing import Optional

from kuka_comm_lib.positions import AxisPos
from kuka_comm_lib.connection import RobotConnection
from kuka_comm_lib.exceptions import RobotAlreadyMovingError
from kuka_comm_lib.positions import CartesianPos


class KukaRobot:
    _connection: RobotConnection

    def __init__(self, host: str, port: int = 7000, asyncio_loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._connection = RobotConnection(host, port)
        self._asyncioloop = asyncio_loop or asyncio.get_event_loop()
        pass

    def move_relative(
        self,
        x_rel: Optional[float] = None,
        y_rel: Optional[float] = None,
        z_rel: Optional[float] = None,
        speed: Optional[float] = None,
        wait_until_complete: bool = False,
    ):
        self._asyncioloop.run_until_complete(
            self.move_relative_async(
                x_rel, y_rel, z_rel, speed=speed, wait_until_complete=wait_until_complete
            )
        )

    async def move_relative_async(
        self,
        x_rel: Optional[float] = None,
        y_rel: Optional[float] = None,
        z_rel: Optional[float] = None,
        speed: Optional[float] = None,
        wait_until_complete: bool = False,
    ):
        """
        move to cartesian coordinates, relative to the current position
        """
        
        opt_pos = await self.get_current_position_async()
        if opt_pos is None:
            raise ValueError("No current position")

        x, y, z, a, b, c = opt_pos
        new_x = x + (x_rel or 0)
        new_y = y + (y_rel or 0)
        new_z = z + (z_rel or 0)

        target = CartesianPos(new_x, new_y, new_z, a, b, c)

        await self._goto(target, speed=speed, wait_until_complete=wait_until_complete)

    def goto(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        a: Optional[float] = None,
        b: Optional[float] = None,
        c: Optional[float] = None,
        speed: Optional[float] = None,
        wait_until_complete: bool = False,
    ):
        self._asyncioloop.run_until_complete(
            self.goto_async(x, y, z, a, b, c, speed=speed, wait_until_complete=wait_until_complete)
        )

    async def goto_async(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        a: Optional[float] = None,
        b: Optional[float] = None,
        c: Optional[float] = None,
        speed: Optional[float] = None,
        wait_until_complete: bool = False,
    ):
        """
        move to cartesian coordinates, relative to the set base (bottom left of conveyor)
        """

        current = await self.get_current_position_async()
        
        if current is None:
            raise ValueError("No current position")

        target = CartesianPos(
            x or current.x,
            y or current.y,
            z or current.z,
            a or current.a,
            b or current.b,
            c or current.c,
        )
        await self._goto(target, speed=speed, wait_until_complete=wait_until_complete)

    def get_current_position(self) -> Optional[CartesianPos]:
        return self._asyncioloop.run_until_complete(self.get_current_position_async())

    async def get_current_position_async(self) -> Optional[CartesianPos]:
        """
        get the current position of the robot
        """
        # {E6POS: X 1991.282, Y 91.03918, Z 1659.515, A 160.2559, B 63.59148, C 161.3706, S 2, T 35, E1 0.0, E2 0.0, E3 0.0, E4 0.0, E5 0.0, E6 0.0}
        pos_string = await self._connection.get_variable("$POS_ACT")
        if pos_string == "":
            return None
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

    def get_current_axis(self) -> Optional[AxisPos]:
        return self._asyncioloop.run_until_complete(self.get_current_axis_async())

    async def get_current_axis_async(self) -> Optional[AxisPos]:
        """
        get the current position of the robot
        """
        # {E6AXIS: A1 -2.820527, A2 -73.70981, A3 80.95905, A4 5.768665, A5 17.77479, A6 -15.32642, E1 0.0, E2 0.0, E3 0.0, E4 0.0, E5 0.0, E6 0.0}
        pos_string = await self._connection.get_variable("$AXIS_ACT")
        if pos_string == "":
            return None
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

    async def _goto(self, target: CartesianPos, speed: Optional[float] = None, wait_until_complete: bool = False):
        """
        *internal*
        move to cartesian coordinates
        """
        if not await self.is_ready_to_move_async():
            raise RobotAlreadyMovingError("Robot is already moving")
        if speed is not None:
            await self.set_speed_async(speed)
        
        print("start move, set IS_RUNNING to 1")
        await self._connection.set_variable("IS_RUNNING", "1")
        
        pos_value_string = f"{{POS: X {target.x}, Y {target.y}, Z {target.z}, A {target.a}, B {target.b}, C {target.c}}}"
        print(pos_value_string)
        await self._connection.set_variable("RUN_FRAME", pos_value_string)
        print("set RUN_FRAME")
        if wait_until_complete:
            print("start wait")
            await self.wait_until_ready_to_move_async()
            print("wait_until_ready_to_move_async done")

    def wait_until_ready_to_move(self):
        return self._asyncioloop.run_until_complete(self.wait_until_ready_to_move_async())

    async def wait_until_ready_to_move_async(self):
        while not await self.is_ready_to_move_async():
            await asyncio.sleep(0.1)

    def is_ready_to_move(self) -> bool:
        return self._asyncioloop.run_until_complete(self.is_ready_to_move_async())

    async def is_ready_to_move_async(self) -> bool:
        in_progress = await self._connection.get_variable("IS_RUNNING")
        if in_progress == "0":
            return True
        print("Robot is already moving: " + in_progress)
        return False

    def connect(self) -> None:
        self._asyncioloop.run_until_complete(self.connect_async())

    async def connect_async(self) -> None:
        await self._connection.connect()

    def is_connected(self) -> bool:
        return self._connection.is_connected()

    def disconnect(self) -> None:
        self._asyncioloop.run_until_complete(self.disconnect_async())

    async def disconnect_async(self) -> None:
        await self._connection.disconnect()

    def set_speed(self, speed: float) -> None:
        self._asyncioloop.run_until_complete(self.set_speed_async(speed))

    async def set_speed_async(self, speed: float) -> None:
        # note: SPEEED is not a typo
        await self._connection.set_variable("SPEEED", str(speed)) 
