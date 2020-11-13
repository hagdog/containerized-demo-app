import yaml
from random import randrange
from pkg_resources import resource_stream

from demoapp.configuredlogger import SeerLogger

log = SeerLogger(__name__, import_level=True)


class Wisdom:
    """In this application that emulates the famous "Magic 8-Ball" toy,
    this class is analogous to the polyhedron inside the Magic 8-Ball
    shell.

    Our seer, however, is a bit more life-like than the plastic toy.
    Our seer learns. He can go out and seek enlightenment again and again.
    The seer's moods often shade his perspective.

    At this time, the only sources of knowledge our seer has found follow the
    same pattern. That is, each perspective contains 10 affirmative,
    5 non-committal, and 5 negative answers.

    This class handles helps the seer to learn and to organize his answers
    according to perspectives.
    """

    def __init__(self):
        self._answers = []
        self._perspective_idx = None
        self._wisdom = None

    def acquire_knowledge(self):
        """The seer is brought to drink at the fount of knowledge.

        If the fount of knowledge has multiple perspectives,
        the seer learns all of them.

        If the seer has already drinken from the fount of knowledge,
        he tries a new perspective.
        """

        # A knowledge file is included in this module's package.
        # So, the location is known.
        stream = resource_stream("demoapp", "data/knowledge.yaml")
        self._wisdom = yaml.load(stream, Loader=yaml.SafeLoader)
        log.debug(f"The seer aquired knowledge.")
        self._update_perspective()

    def answer_question(self):
        return self._answers[randrange(0, len(self._answers))]

    def _get_new_perspective(self):
        new_idx = 0
        num_of_perspectives = len(self._wisdom)
        log.debug(f"The seer has {num_of_perspectives} perspectives.")
        if num_of_perspectives > 1:
            new_idx = self._perspective_idx
            # Don't use the same perspective again.
            while new_idx == self._perspective_idx:
                # _wisdom is a list of perspectives
                new_idx = randrange(0, num_of_perspectives)

        return new_idx

    def _update_perspective(self):
        if self._perspective_idx is None:
            # Only None at object initialization.
            # The first perspective is the startup default.
            self._perspective_idx = 0
        else:
            self._perspective_idx = self._get_new_perspective()

        self._answers = self._wisdom[self._perspective_idx]["answers"]
        log.debug(
            f"Updated answers for: perspective = {self.perspective}, "
            f"perspective_idx: {self._perspective_idx}"
        )

    @property
    def perspective(self):
        return self._wisdom[self._perspective_idx]["perspective"]

    @property
    def perspective_index(self):
        return self._perspective_idx

    @property
    def is_meager(self):
        # The seer's level of knowledge.
        return not bool(self._wisdom)
