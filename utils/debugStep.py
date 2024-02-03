

class DebugStep:
    def __init__(self, time: float, debugTuple, prevDT):
        from utils.debugTuple import DebugTuple

        # DT that where processed by this step or before this step
        self.debugTuple: DebugTuple = debugTuple  # This is the DT that results after the step (REDO)
        self.prevDebugTuple: DebugTuple = prevDT  # This is the DT before the step (UNDO)

        self.time = time
