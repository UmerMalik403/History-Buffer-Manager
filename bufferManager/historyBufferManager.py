from typing import Optional, Dict, List

from utils.debugStep import DebugStep
from utils.debugTuple import DebugTuple

# [Alper] imports
import tempfile
import os   
import dill
from pathlib import Path
#
class HistoryBufferManager:
    def __init__(self, debugger):
        from utils.pipelineDebugger import PipelineDebugger
        self._pipelineDebugger: PipelineDebugger = debugger

        # Memory limit of each type (None = Infinite)
        self._mainMemoryLimit: Optional[int] = None  # In MBytes
        self._storageMemoryLimit: Optional[int] = None  # In MBytes

        # Current memory values
        self._currentMainMemorySize = 0  # In bytes
        self._currentStorageMemorySize = 0  # In bytes

        # Stores for each DT all steps it is registered in (prevT & dt)
        self._historyDtLookup: Dict[DebugTuple, List[DebugStep]] = dict()

        # lookup table with the mapping uuid -> DT object
        self._DtLookup: Dict[str, DebugTuple] = dict()

        #### [Alper] initialize the temporary directory for python shelve file
        self._storageDir = tempfile.TemporaryDirectory() # the temporary directory will be deleted with its contents after execution
        self._storagePath = self._storageDir.name
        ####

    # ------------------------------ INTERFACE ------------------------------
    def reset(self):
        self._currentMainMemorySize = 0
        self._currentStorageMemorySize = 0

        # Clear storage

        for dt in self._historyDtLookup:
            self._removeFromStorage(dt)

            dt.delete()

        self._historyDtLookup.clear()
        #### [Alper]
        self._DtLookup.clear()
        ####
        
    def changeMemoryLimit(self, mainMemorySize: Optional[int], storageMemorySize: Optional[int]):
        self._mainMemoryLimit = mainMemorySize
        self._storageMemoryLimit = storageMemorySize

        # Do not modify buffer here, only modify buffers in _adjustBuffer

    def registerStep(self, step: DebugStep):
        # Register both DebugTuples [DT]

        self._registerStepDT(step, step.prevDebugTuple)
        self._registerStepDT(step, step.debugTuple)

        # Now check if our memory limits are reached

        self._adjustBuffer()

    def requestDT(self, dt: DebugTuple):
        if not dt.isLoaded():
            #### [Alper] try loading the DT, return None if there's not a file
            try:
                self._loadDT(dt)
            except FileNotFoundError: # file is already deleted along with the DT
                return None

    # -------------------------------- BUFFER -------------------------------
    def _storeDT(self, dt: DebugTuple):
        # TODO: Add functionality for store to main memory or storage
        #       DT can be unloaded with dt.unload if moved to storage from main memory
        #       Currently implemented for keeping all data in main memory

        #### [Alper] store the DT object in a file named with its unique uuid
        filepath = os.path.join(self._storagePath, dt.uuid)
        with open(filepath, "wb") as h:
            dill.dump(dt, h)
        
        # increase the storage size as we stored the DT object on the filesystem
        # also remove the current DT's total memory from the `_currentMainMemorySize`, 
        # we'll update it after unloading the dt.
        self._currentStorageMemorySize += os.path.getsize(filepath)
        # now unload the DT
        dt.unload()
        # update the memory
        dt._updateMemorySize()
        #### the line below will update the currently allocated memory for the DT 

        self._currentMainMemorySize += dt.getMemorySize()

        print("Current Memory: Main = " + str(self._currentMainMemorySize / 1000000) + " MBs | Storage = " + str(self._currentStorageMemorySize / 1000000))

    def _adjustBuffer(self):
        # TODO: Check here if the memory limit is reached for main memory and storage
        #       Currently implemented for keeping all data in main memory

        # Adjust buffer if main memory limit is reached

        if self._mainMemoryLimit is not None:
            memBytes = self._mainMemoryLimit * 1000000
            while self._currentMainMemorySize > memBytes:
                self._removeOldestStepFromHistory()

        #### [Alper]
        if self._storageMemoryLimit is not None:
            memBytes = self._storageMemoryLimit * 1000000
            # get the stored files ordered in the descending modified time order so the first element will be the first modified one 
            while self._currentStorageMemorySize > memBytes:
                storedFiles = iter(sorted(Path(self._storagePath).iterdir(), key=os.path.getmtime, reverse=True))
                oldestFilePath = next(storedFiles)
    
                # update the storage memory
                self._currentStorageMemorySize -= os.path.getsize(oldestFilePath)
                # remove the file 
                os.remove(oldestFilePath)
        ####

    def _removeFromStorage(self, dt: DebugTuple):
        # TODO: Add functionality to permanently remove from storage
        #       Currently implemented for keeping all data in main memory
        #### [Alper]
        if dt.uuid in os.listdir(self._storagePath):
            # remove the stored file from the filesystem (storage)
            storedDTPath = os.path.join(self._storagePath, dt.uuid)
            # update the storage size        
            self._currentStorageMemorySize -= os.path.getsize(storedDTPath)
            # load the item to the memory
            with open(storedDTPath, "rb") as h:
                dtObj = dill.load(h)
            dt.load(dtObj._tuple, dtObj._data)
            # remove the file from filesystem
            os.remove(storedDTPath)
        else:
            # if dt.uuid not in the storagePath, then it should be already deleted when the storage memory exceeded.
            pass
        ####

    def _onDebugTupleMemoryChange(self, dt: DebugTuple, memoryDelta: int):
        # TODO: Keep track of tuples if they are on main memory or storage and update
        #       Only the dt.getData value will be updated, but never the dt.getTuple().data!
        #       Currently implemented for keeping all data in main memory
        # Update main memory if this dt is still registered
        if self._historyDtLookup.get(dt) is not None:
            self._currentMainMemorySize += memoryDelta

            #### [Alper]
            # read the file
            with open(os.path.join(self._storagePath, dt.uuid), "rb") as h:
                dtObj = dill.load(h)
            # update the `_data`
            dtObj._data = dt._data
            # then save the file again
            with open(os.path.join(self._storagePath, dt.uuid), "wb") as h:
                dill.dump(dtObj, h)
            ####
            print("Current Memory: Main = " + str(self._currentMainMemorySize / 1000000) + " MBs | Storage = " + str(self._currentStorageMemorySize / 1000000))

    def _loadDT(self, dt: DebugTuple):
        # TODO: Load from storage
        #       Use dt.uuid to identify the dt
        #       Later at this point we could apply some smart caching to load also the next elements

        #### [Alper]
        with open(os.path.join(self._storagePath, dt.uuid), "rb") as h:
            data = dill.load(h)
        dt.load(data._tuple, data._data)
        dt._updateMemorySize()
        ####

    # -------------------------------- UTILS --------------------------------

    def _registerStepDT(self, step: DebugStep, dt: DebugTuple):
        if dt is None:
            return

        stepList = self._historyDtLookup.get(dt)

        if stepList is None:
            self._historyDtLookup[dt] = [step]
            #### [Alper] add the DT to the hash map
            self._DtLookup[dt.uuid] = dt
            ####
            dt.registerMemoryChangeCallback(self._onDebugTupleMemoryChange)

            self._storeDT(dt)
        else:
            stepList.append(step)
            self._historyDtLookup[dt] = stepList

    def _removeOldestStepFromHistory(self):
        removed = self._pipelineDebugger.removeStep(0)

        if removed is None:
            return

        # removed.debugTuple.debugger.unregisterStep(removed)

        # Unregister DT from history lookup
        self._unregisterStepDT(removed, removed.prevDebugTuple)
        self._unregisterStepDT(removed, removed.debugTuple)

    def _unregisterStepDT(self, step: DebugStep, dt: DebugTuple):
        if dt is None:
            return

        stepList = self._historyDtLookup.get(dt)
        stepList.remove(step)
        self._historyDtLookup[dt] = stepList
        # Permanently remove this dt since it is no longer used in the history

        if len(stepList) == 0:
            del self._historyDtLookup[dt]
            #### [Alper]
            # remove the DT from the hash map
            del self._DtLookup[dt.uuid]
            # update the current memory size
            # (this is not a perfect solution, memory update shouldn't
            # be done like this. `_updateMemorySize` method should be enough but 
            # it doesn't work as it's intended I guess, the memory update wasn't accurate
            # when I just use the `_updateMemorySize` method.)
            self._currentMainMemorySize -= dt.getMemorySize()
            # remove the DT from the storage and then delete its data
            self._removeFromStorage(dt)
            dt.delete()
            # finally update memory
            dt._updateMemorySize()
            ####

    # -------------------------------- GETTER --------------------------------

    def getMainMemorySize(self) -> int:
        return self._currentMainMemorySize

    def getStorageMemorySize(self) -> int:
        return self._currentStorageMemorySize
