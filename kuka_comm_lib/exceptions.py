class RobotException(Exception):
    pass


class RobotError(RobotException):
    pass


class RobotNotConnectedError(RobotError):
    pass


class RobotAlreadyMovingError(RobotError):
    pass
