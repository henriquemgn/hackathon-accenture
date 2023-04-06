import time
from uuid import uuid4
from typing import Union, List
from eventfactory import Detection
from eventfactory import EventEndedSignal, EventStartedSignal
from eventfactory.pipeline.steps import BusinessLogic


class Event():
    """
    A class representing an event detected in a video frame.

    Attributes:
    -----------
    detection : Detection
        The detection asociated with the event
    num_detected_frames : int
        The number of frames in which the event has been detected
    creation_time : float
        The time at which the vent was first created
    ttl : int
        The time-to-live for the event in seconds

    Methods:
    --------
    _reset_ttl() -> None:
        Resets the time-to-live value for the event
    no_detection() -> None:
        Decreases current time-to-live value when the object is not detected in
        the current frame
    new_detection(detection: Detection) -> None:
        Updates the detection for the event and resets its time-to-live value
    is_expired() -> bool:
        Returns True is the event has expired, i.e., if its time-to-live has
        elapsed
    """

    def __init__(self, detection: Detection, ttl: int) -> None:
        self.detection = detection
        self.num_detected_frames = 1
        self.creation_time = time.time()
        self.ttl = ttl
        self.current_ttl = self.ttl

    def _reset_ttl(self) -> None:
        self.current_ttl = self.ttl

    def no_detection(self) -> None:
        self.current_ttl -= 1

    def new_detection(self, detection: Detection) -> None:
        """
        Updates the detection for the event and resets its time-to-live value.

        Parameters:
        -----------
        detection : Detection
            The new detection associated with the event
        """
        self.detection = detection
        self.num_detected_frames += 1
        self._reset_ttl()

    def is_expired(self) -> bool:
        return self.current_ttl <= 0


class RoIBusinessLogic(BusinessLogic):
    """
    Class representing the business logic for detecting events in a video frame

    Parameters:
    -----------
    total_frames : int
        The total number of frames for which an event needs to be detected to
        be considered started.
    ttl : int
        The number of frames for which an object needs to not be detected for an
        event to be considered ended.

    Methods:
    --------
    _get_starting_events() -> List[EventStartedSignal]:
        Returns a list of new events that have just started.
    _get_ending_events() -> List[EventEndedSignal]:
        Returns a list of events that have just ended.
    _is_start_event(key: str, event: Event) -> bool:
        Returns True if the event should be considered started.
    _is_end_event(key: str) -> bool:
        Returns True if the event should be considered ended.
    process(detection: Detection) -> List[Union[EventEndedSignal,
                                                EventStartedSignal]]:
        Processes a new detection and returns a list of events that have
        started of ended.
    """

    def __init__(self, total_frames: int, ttl: int):
        self._total_frames = total_frames
        self._event_dict = {}
        self._active_events = {}
        self._ttl = ttl

    def _get_starting_events(self) -> List[EventStartedSignal]:
        """
        Identifies objects that have just appeared and generates the
        corresponding event signals.

        :return: A list of EventStartedSignal objects representing the events
        of new object appearances.
        """
        events = []

        for k, event in self._event_dict.items():
            if self._is_start_event(k, event):
                event_id = str(uuid4())
                events.append(EventStartedSignal(event_id, event.detection))
                self._active_events[k] = event_id

        return events

    def _get_ending_events(self) -> List[EventEndedSignal]:
        """
        Identifies objects that have disappeared and generates the
        corresponding event signals.

        :return: A list of EventEndedSignal objects representing the events
        of object disappearances.
        """
        events = []
        del_events = []

        for k, event in self._event_dict.items():
            if not event.is_expired():
                continue

            del_events.append(k)

            if self._is_end_event(k):
                events.append(EventEndedSignal(self._active_events[k],
                                               event.detection))
                del self._active_events[k]

        for k in del_events:
            del self._event_dict[k]

        return events

    def _is_start_event(self, key: str, event: Event) -> bool:
        """
        Determines if a detected object should be considered as a new event.

        :param key: The key associated with the detected object in the event
        dictionary.
        :param event: The Event object associated with the detected object.
        :return: True if the detected object should be considered as a newly
        appearing object, False otherwise.
        """
        if event.num_detected_frames < self._total_frames:
            return False

        if key in self._active_events:
            return False

        return True

    def _is_end_event(self, key: str) -> bool:
        """
        Checks whether an event is still active.

        :param key: The key associated with the detected object in the event
        dictionary.
        :return: True if event is not active, False otherwise.
        """
        if key not in self._active_events:
            return False

        return True

    def process(self,
                detection: Detection
                ) -> List[Union[EventEndedSignal, EventStartedSignal]]:
        """
        Process a detection and generate a list of event signals based on its
        properties and behavior.

        Parameters:
        -----------
            detection (Detection): A Detection object containing information
            about the objects detected in a video frame.

        Returns:
            List[Union[EventEndedSignal, EventStartedSignal]]: A list of event
            signals generated based on the properties and behavior of the
            objects detected in the video frame. Each signal is an instance of
            either the EventStartedSignal or EventEndedSignal class.
        """
        current_frame_classes = set()
        for pred in detection["predictions"]:
            current_frame_classes.add(pred["classId"])
            if pred["classId"] not in self._event_dict:
                new_event = Event(detection, self._ttl)
                self._event_dict[pred["classId"]] = new_event
            else:
                self._event_dict[pred["classId"]].new_detection(detection)

        active_events_classes = set(self._event_dict.keys())
        classes_not_in_frame = active_events_classes - current_frame_classes

        for cls in classes_not_in_frame:
            self._event_dict[cls].no_detection()

        start_events = self._get_starting_events()
        end_events = self._get_ending_events()

        all_events = start_events + end_events

        return all_events if all_events else None
