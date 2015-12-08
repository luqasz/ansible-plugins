# -*- coding: UTF-8 -*-
"""Add task and playbook profiling."""

import time
from ansible.utils import display


class CallbackModule(object):

    """Add task and playbook profiling."""

    def __init__(self):
        """Record playbook start time."""
        self.start_time = time.time()
        self.end_time = None
        self.stats = {}
        self.current_task = None
        self.top_n = 10

    def _record_current_task(self, name):
        """Log start of task."""
        self._record_last_task()
        # Record the start time of the current task
        self.current_task = name
        self.stats[self.current_task] = time.time()

    def _record_last_task(self):
        """Record the running time of the last executed task."""
        if self.current_task is not None:
            self.stats[self.current_task] = time.time() - self.stats[self.current_task]

    def playbook_on_task_start(self, name, is_conditional):
        """Executed when task starts."""
        self._record_current_task(name)

    def v2_playbook_on_handler_task_start(self, task):
        """Executed when handler starts."""
        self._record_current_task('HANDLER: ' + task.name)

    @property
    def results(self):
        """Sort tasks by their running time. Longest first."""
        return sorted(
            self.stats.items(),
            key=lambda value: value[1],
            reverse=True,
        )

    @property
    def playbook_runtime(self): # noqa
        if not self.end_time:
            self.end_time = time.time()
        return self.end_time - self.start_time

    @staticmethod
    def format_time(hours, minutes, seconds):
        """
        Format hours, minutes and seconds to a human readable form.

        If hours or minutes == 0, they are not returned.
        Always return formatted seconds.
        """
        hours = '{}h'.format(hours) if hours else ''
        minutes = '{}m'.format(minutes) if minutes else ''
        seconds = '{0:.01f}s'.format(seconds)
        return ' '.join((hours, minutes, seconds))

    @staticmethod
    def extract_time_units(seconds):
        """Extract hours, minutes, seconds."""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return int(h), int(m), s

    def display_result(self, name, elapsed):
        """Display nicelly formated result."""
        units = self.extract_time_units(elapsed)
        display("{0:<65}{1:>14}".format(name, self.format_time(*units)))

    def display_results(self):
        """Display top n task results."""
        display('Top {} tasks:'.format(self.top_n))
        for name, elapsed in self.results[:self.top_n]:
            self.display_result(name, elapsed)

    def playbook_on_stats(self, stats):
        """Executed on PLAY RECAP."""
        self._record_last_task()
        self.display_result('Playbook runtime', self.playbook_runtime)
        self.display_results()
