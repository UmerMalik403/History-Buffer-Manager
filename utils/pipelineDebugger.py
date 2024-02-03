from enum import Enum
from typing import List, Optional

from bufferManager.historyBufferManager import HistoryBufferManager
from utils.debugStep import DebugStep


class HistoryState(Enum):
    INACTIVE = 1  # Pipeline is running
    ACTIVE = 2  # Pipeline stopped
    TRAVERSING_FORWARD = 3  # Pipeline stopped and traversing fwd
    TRAVERSING_BACKWARD = 4  # Pipeline stopped and traversing bwd

    def isActive(self) -> bool:
        return self != HistoryState.INACTIVE


class PipelineDebugger:
    def __init__(self):
        self._steps: List[DebugStep] = list()
        self._bufferManager = HistoryBufferManager(self)

        self._historyState = HistoryState.INACTIVE

        self._currentStep = 0

    def registerStep(self, step: DebugStep):
        self._steps.append(step)
        self._currentStep = len(self._steps) - 1

        self._bufferManager.registerStep(step)

    def iterate(self, forward: bool):
        if forward:
            self._historyState = HistoryState.TRAVERSING_FORWARD

            for i in range(self._currentStep + 1, len(self._steps)):
                step = self._steps[i]

                self._bufferManager.requestDT(step.debugTuple)
                self._currentStep = i
        else:
            self._historyState = HistoryState.TRAVERSING_BACKWARD

            for i in range(self._currentStep, -1, -1):
                step = self._steps[i]

                if step.prevDebugTuple is not None:
                    self._bufferManager.requestDT(step.prevDebugTuple)

                self._currentStep = i

    def changeBufferMemoryLimits(self, mainMemoryLimit: Optional[int], storageMemoryLimit: Optional[int]):
        self._bufferManager.changeMemoryLimit(mainMemoryLimit, storageMemoryLimit)

    def removeStep(self, index: int) -> Optional[DebugStep]:
        if len(self._steps) <= index:
            return None

        rmd = self._steps.pop(index)

        self._currentStep = min(self._currentStep, len(self._steps) - 1)

        # When removing a step we delete the DT, so we need to remove them from other steps

        return rmd

    def getCurrentStepID(self) -> int:
        return self._currentStep

    def getGlobalStep(self, stepID: int):
        return self._steps[stepID]

    def getGlobalStepCount(self) -> int:
        return len(self._steps)

    def getHistoryState(self) -> HistoryState:
        return self._historyState
