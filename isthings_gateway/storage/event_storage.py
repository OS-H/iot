from logging import getLogger
from abc import ABC, abstractmethod

log = getLogger("storage")

class EventStorage(ABC):

    @abstractmethod
    def put(self, event):
        pass

    @abstractmethod
    def get_event_pack(self):
        # Returns max "10" events from pack
        pass

    @abstractmethod
    def event_pack_processing_done(self):
        # Indicates that events from previous "get_event_pack" may be cleared
        pass

    @abstractmethod
    def get_event_count(self):
        # Returns the number of events in the queue
        pass
