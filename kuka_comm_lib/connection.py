from kuka_comm_lib.exceptions import RobotNotConnectedError


import asyncio
import struct


class RobotConnection:
    host: str
    port: int

    _conn_reader: asyncio.StreamReader | None
    _conn_writer: asyncio.StreamWriter | None

    channel_lock: asyncio.Lock

    def __init__(self, host: str, port: int = 7000) -> None:
        self.host = host
        self.port = port
        self.channel_lock = asyncio.Lock()

    async def connect(self):
        if self.is_connected():
            return
        self._conn_reader, self._conn_writer = await asyncio.open_connection(
            self.host, self.port
        )

    def is_connected(self) -> bool:
        if self._conn_reader is None or self._conn_writer is None:
            return False
        if self._conn_writer.is_closing():
            print("Connection was closed unexpectedly")
            self._conn_reader = None
            self._conn_writer = None
            return False
        return True

    async def disconnect(self):
        if (
            self.is_connected()
            and self._conn_reader is not None
            and self._conn_writer is not None
        ):
            self._conn_writer.close()
        self._conn_reader = None
        self._conn_writer = None

    @property
    def reader(self) -> asyncio.StreamReader:
        if (
            self._conn_reader is None
            or self._conn_writer is None
            or self._conn_writer.is_closing()
        ):
            raise RobotNotConnectedError("Robot is not connected")
        return self._conn_reader

    @property
    def writer(self) -> asyncio.StreamWriter:
        if (
            self._conn_reader is None
            or self._conn_writer is None
            or self._conn_writer.is_closing()
        ):
            raise RobotNotConnectedError("Robot is not connected")
        return self._conn_writer

    @staticmethod
    def encode_message(tag: int, msgtype: int, contents: bytes) -> bytes:
        # print(len(contents))
        header = struct.pack("!HHB", tag, len(contents) + 1, msgtype)
        return header + contents

    async def get_variable(self, variable_name: str) -> str:
        message = struct.pack("!H", len(variable_name)) + variable_name.encode(
            "utf-16le"
        )
        async with self.channel_lock:
            self.writer.write(self.encode_message(0, 4, message))
            header = await self.reader.read(5)
            (tag, length, msgtype) = struct.unpack("!HHB", header)
            body = await self.reader.read(length - 1)
        return body[2:-3].decode("utf-16le")

    async def set_variable(self, variable_name: str, value: str):
        message = (
            struct.pack("!H", len(variable_name))
            + variable_name.encode("utf-16le")
            + struct.pack("!H", len(value))
            + value.encode("utf-16le")
        )
        async with self.channel_lock:
            self.writer.write(self.encode_message(0, 5, message))
            header = await self.reader.read(5)
            (tag, length, msgtype) = struct.unpack("!HHB", header)
            body = await self.reader.read(length - 1)
        print(body[2:-3].decode("utf-16"))
