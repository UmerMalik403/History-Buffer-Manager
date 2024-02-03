import random
import string
import time
from typing import Dict

import numpy as np

from utils.customClass import CustomClass
from utils.debugStep import DebugStep
from utils.debugTuple import DebugTuple
from utils.pipelineDebugger import PipelineDebugger
from utils.tuple import Tuple

debugger = PipelineDebugger()

# ------------------------ UTILS ---------------------------------


def _getRandomData():
    mode = random.randint(0, 5)

    if mode == 0:  # float
        return random.random()
    elif mode == 1:  # array of floats (between 10 and 50 values)
        return np.random.uniform(low=0.5, high=13.3, size=(random.randint(10, 50),))
    elif mode == 2:  # string (between 10 and 50 chars)
        return ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(10, 50)))
    elif mode == 3:  # image between 300x300px and 600x600px
        rgb = np.random.randint(255, size=(random.randint(300, 600), random.randint(300, 600), 3), dtype=np.uint8)
        return rgb
    elif mode == 4:  # dict with string and int value
        return {"key": ''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(10, 50))), "key2": random.randint(0, 100)}
    elif mode == 5:  # custom object
        return CustomClass(''.join(random.choice(string.ascii_lowercase) for i in range(random.randint(10, 50))), random.randint(10, 999))


def _createStep(identifier, lastStepLookup):
    dt = DebugTuple(Tuple((_getRandomData(),)))

    lastStep = lastStepLookup.get(identifier)
    lastDT = lastStep.debugTuple if lastStep is not None else None

    # In case DT got deleted
    if lastDT is not None and lastDT.getTuple() is None:
        lastDT = None

    step = DebugStep(time.time(), dt, lastDT)
    lastStepLookup[identifier] = step

    debugger.registerStep(step)

    # Register a few attributes
    for i in range(random.randint(1, 3)):
        dt.registerAttribute("testAttr" + str(i), _getRandomData())

# ----------------------------------------------------------------


def registerSteps(steps: int):
    print("Register " + str(5000) + " steps")

    ids = ["A", "B", "C", "D", "E"]

    lastStepLookup: Dict[str, DebugStep] = dict()

    for i in range(steps):
        print("STEP: %d"%(i+1))
        _createStep(random.randint(0, len(ids) - 1), lastStepLookup)

    print("----------------------------------------------------")


def main():
    debugger.changeBufferMemoryLimits(50, 50)  # Set main memory limit and storage limit in MBytes (None if infinite)

    registerSteps(2000)

    print("Traverse history backward, starting at index " + str(debugger.getCurrentStepID()))

    debugger.iterate(False)

    print("Traverse history forward, starting at index " + str(debugger.getCurrentStepID()))

    debugger.iterate(True)


if __name__ == "__main__":
    main()
