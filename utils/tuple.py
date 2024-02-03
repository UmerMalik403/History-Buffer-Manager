import time
import uuid

from pympler import asizeof


class Tuple:
    def __init__(self, data: tuple):
        self.uuid = str(uuid.uuid4().hex)

        self.data: tuple = data

        self.eventTime = time.time()  # Time when this specific tuple was created

        self.socketID = None  # Always the IN socket of the operator that processes the tuple

    def calcMemorySize(self) -> float:
        # Returns bytes

        if self.data is None:
            return 0

        totalSize = 0

        for i in range(0, len(self.data)):
            d = self.data[i]
            totalSize += d.getDataSize() if hasattr(d, "getDataSize") else asizeof.asizeof(d)

        return totalSize
