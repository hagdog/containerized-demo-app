import os
import pickle
import signal
from enum import Enum

from demoapp.configuredlogger import SeerLogger
from demoapp.sidecarinterface import SidecarNotifier
from demoapp.wisdom import Wisdom

log = SeerLogger(__name__, import_level=True)


class Event(Enum):
    awaken = "awaken"
    overexert = "overexert"
    rally = "rally"
    reflect = "reflect"
    sleep = "sleep"


# Signals handled in seerpsyche State instances.
supported_signals = [
    signal.SIGHUP,
    signal.SIGINT,
    signal.SIGUSR1,
    signal.SIGUSR2,
]

sign_num_to_event = {
    signal.SIGHUP.value: Event.reflect,
    signal.SIGINT.value: Event.overexert,
    signal.SIGUSR1.value: Event.awaken,
    signal.SIGUSR2.value: Event.rally,
}

# A convenience map for logging purposes.
sig_num_to_name = {
    signal.SIGHUP.value: "SIGHUP",
    signal.SIGINT.value: "SIGINT",
    signal.SIGUSR1.value: "SIGUSR1",
    signal.SIGUSR2.value: "SIGUSR2",
}


class Seer:
    """The Seer ia all-seeing and all-knowing, NOT.

    A Seer instance, or seer, is a stateful object that forms
    the core of the seer program. The seer has a REST interface that is uses
    to answer questions for his acolytes. The seer has a socket interface that
    it uses to talk to the sidecar. The sidecar acts as an intermediary
    between the seer application and the TestAssitant. TestAssitant is always
    using its testdriver container to listen to the sidecar for updates
    on the seer.

    Args:
        sidecar_socket_file (str): The socket file used to communicate with
            a sidecar container that is joined with a system-under-test
            (SUT) container. This app sends status updates over the socket.
        pid (int): In normal use, the PID is 1 in a Docker container.
            In unit testing, the PID varies.
    """

    def __init__(self, memories_file, messages_path, pid, sidecar_socket_file):
        log.debug("Seer instance initializing.")
        # The Seer sends notifications to the SUT via the sidecar.
        self._messages_path = messages_path
        self.notifier = SidecarNotifier(sidecar_socket_file, messages_path)

        # The location is used for saving and restoring memories.
        self._memories_file = memories_file
        if os.path.exists(memories_file):
            log.debug("Memories found. Recalling experiences.")
            self.wisdom = pickle.load(open(memories_file, "rb"))
            os.remove(memories_file)
        else:
            log.debug("No memories found. Using book knowledge.")
            self.wisdom = Wisdom()

        self.state = Waking(
            notifier=self.notifier,
            pid=pid,
            wisdom=self.wisdom,
        )
        # Supported O/S signals must be mapped to handler functions.
        # The handlers operate on the self.state object.
        self._register_event_signals(supported_signals)
        self._register_shutdown_signal(signal.SIGTERM)

        # Give the waking seer a nudge to make him available.
        self.event(Event.rally)

    def event(self, event):
        """This method sends events to the state machine managed by this
        object. That state machine is accessed using the 'state'  attribute
        of this object. When this method returns, the state machine will
        have been updated in response to the event.

        Args:
            event (Event): An event is an activity that affects the seer
                application. This object must receive events in order for
                the application to respond to the event.
        """
        self.state = self.state.on_event(event)

    def _register_event_signals(self, signals):
        # Associate signals with the a signal handler that
        # translates signals to seer Event's.
        for sig in signals:
            signal.signal(sig, self._handle_event_signal)
            log.debug(
                f"Registered signal {sig.name} ({sig.value}) "
                f"to handler: {self._handle_event_signal.__name__}"
            )

    def _register_shutdown_signal(self, sig):
        # Associate the designated signal with the signal handler
        # that manages shutdowns.
        log.debug(
            f"Registered signal: {sig.name} ({sig.value}) "
            f"to handler {self._handle_shutdown_signal.__name__}"
        )
        signal.signal(sig, self._handle_shutdown_signal)

    def register_service_interface_shutdown(self, service_interface_shutdown):
        """Register the function that shuts down the app interface with
        the shutdown method.

        Args:
            service_interface_shutdown (function): The function that
                terminates the HTTP REST server. Parameters are not passed
                to this function.
        """
        self._service_interface_shutdown = service_interface_shutdown

    def _handle_event_signal(self, signum, sigstack):
        """This signal handler processes asynchronous events by translating
        the O/S signal events to application events and then sending the
        events to the seer state machine.
        """
        log.debug(
            "signal handling requested: "
            f"{sig_num_to_name[signum]} ({signum})"
        )
        if signum in sign_num_to_event.keys():
            event = sign_num_to_event[signum]
            self.event(event)
            log.debug(
                "signal handling performed: "
                f"{sig_num_to_name[signum]} ({signum})"
            )

    def _handle_shutdown_signal(self, signum, sigstack):
        """This signal handler performs a series of operations that:
        * Preserve the current knowledge and perspective of the seer.
        * Shut down the REST interface.
        * Update the seer state machine.
        """
        log.debug(f"_handle_shutdown_signal({signum})")

        log.info("Saving memories.")
        pickle.dump(self.wisdom, open(self._memories_file, "wb"))
        self.event(Event.sleep)

        try:
            self._service_interface_shutdown()
        except AttributeError:
            # A shutdown signal was received
            # before the app service register its shutdown function.
            pass


class State:
    """
    The State object provides some utility functions for the
    individual states within the state machine.
    """

    def __init__(self, **config):
        # The config-as-a-dictionary keeps initialization code neat.
        try:
            # At state transitions.
            self.config.update(config)
        except AttributeError:
            # At state machine creation.
            self.config = config

    def on_event(self, event):
        """Non-supported state transitions are not errors. Just, no-ops.
        For example, ignore a sleep event while in the Sleep state.
        """
        return self

    @property
    def notifier(self):
        return self.config["notifier"]

    @property
    def wisdom(self):
        return self.config["wisdom"]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__


class Available(State):
    """The seer application is fully operational. The seer can respond to
    questions while Available. The sidecar is notified that the app is ready.
    """

    def __init__(self, **config):
        log.debug("Seer.State transitioned to Available.")
        super().__init__(**config)

        if self.notifier.has_pending_injections:
            _, self.config["pid"] = self.notifier.send_injected_messages()

        self.notifier.send_ready_update(ready=True, pid=self.config["pid"])
        log.debug(
            "Notification sent to sidecar: "
            f"ready=True, pid={self.config['pid']}."
        )

    def on_event(self, event):
        if event is Event.reflect:
            """
            If the fount of knowledge has multiple perspectives, it is
            not possible to predict which perspective the seer
            will come away with. You can be sure, however, that his perspective
            changes each time he drinks from the fountain.
            """
            log.debug("Learning while available.")
            self.wisdom.acquire_knowledge()
            return self

        if event is Event.overexert:
            log.debug(f"Available.on_event({event.value}).")
            return Napping(**self.config)

        if event is Event.sleep:
            log.debug(f"Available.on_event({event.value}).")
            return Sleeping(**self.config)

        # See super.on_event.
        return self


class Napping(State):
    """The seer does not answer questions while he is Napping. But, he
    can sleep-learn. The sidecar is notified that the app is not ready.
    """

    def __init__(self, **config):
        log.info("Seer.State transitioned to Napping.")
        super().__init__(**config)
        log.debug(
            "Notification sent to sidecar: "
            f"ready=False, pid={self.config['pid']}."
        )
        self.notifier.send_ready_update(ready=False, pid=self.config["pid"])

    def on_event(self, event):
        if event is Event.awaken:
            log.debug(f"Napping.on_event({event.value}).")
            return Waking(**self.config)

        if event is Event.reflect:
            log.debug(f"Napping.on_event({event.value}).")
            self.wisdom.acquire_knowledge()
            return self

        if event is Event.sleep:
            log.debug(f"Napping.on_event({event.value}).")
            return Sleeping(**self.config)

        # See super.on_event.
        return self


class Sleeping(State):
    """The seer does nothing while Sleeping.

    The sidecar is notified that the app is no longer ready.
    """

    def __init__(self, **config):
        log.debug("Seer.State transitioned to Sleeping.")
        super().__init__(**config)

        log.debug(
            "Notification sent to sidecar: "
            f"ready=False, pid={self.config['pid']}."
        )
        self.notifier.send_ready_update(ready=False, pid=self.config["pid"])


class Waking(State):
    """While waking, the seer gains wisdom by drinking from the fount of
    knowledge. The sidecar is notified that a unidentified seer is stirring.
    """

    def __init__(self, **config):
        log.debug("Seer.State transitioned to Waking.")
        super().__init__(**config)

        if self.wisdom.is_meager:
            self.wisdom.acquire_knowledge()

        self.notifier.send_ready_update(ready=True, pid=0)
        log.debug("Notification sent to sidecar: " f"ready=True, pid=0.")

    def on_event(self, event):
        if event is Event.rally:
            log.debug(f"Waking.on_event({event.value}).")
            return Available(**self.config)

        if event is Event.sleep:
            log.debug(f"Waking.on_event({event.value}).")
            return Sleeping(**self.config)

        # See super.on_event.
        return self
