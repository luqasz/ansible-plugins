# -*- coding: UTF-8 -*-
"""Add task and playbook profiling."""

from time import time as timer
from collections import namedtuple
from ansible.utils import display

StartedTask = namedtuple('StartedTask', ('name', 'time'))


class CallbackModule(object):

    """Task and playbook profiling."""

    # How many tasks to display at the end.
    top_tasks = 10

    def __init__(self):
        """Record playbook start time."""
        self.playbook_start_time = None
        self.playbook_end_time = None
        self.recorded_tasks = list()

    def _record_task(self, name):
        """Record current task start time."""
        self.recorded_tasks.append(StartedTask(name=name, time=timer()))

    def playbook_on_start(self):
        """Excuted when playbook starts."""
        self.playbook_start_time = timer()

    def v2_playbook_on_start(self, playbook):
        """Excuted when playbook starts."""
        self.playbook_on_start()

    def playbook_on_task_start(self, name, is_conditional):
        """Executed when task starts."""
        self._record_task(name)

    def v2_playbook_on_handler_task_start(self, task):
        """Executed when handler starts."""
        self._record_task('HANDLER: ' + task.name)

    @property
    def elapsed(self):
        """Count elapsed time for tasks."""
        start_tasks = self.recorded_tasks
        next_tasks = self.recorded_tasks[1:] + [StartedTask(name='PLAYBOOK END', time=self.playbook_end_time)]
        return (
                StartedTask(name=start_task.name, time=(next_task.time - start_task.time))
                for start_task, next_task in zip(start_tasks, next_tasks)
                )

    @property
    def results(self):
        """Sort tasks by their runtime. Longest first."""
        return sorted(
            self.elapsed,
            key=lambda task: task.time,
            reverse=True,
        )

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
        display('Top {} tasks:'.format(self.top_tasks))
        for name, elapsed in self.results[:self.top_tasks]:
            self.display_result(name, elapsed)

    def playbook_on_stats(self, stats):
        """Executed on PLAY RECAP."""
        self.playbook_end_time = timer()
        self.display_result('Playbook runtime', (self.playbook_end_time - self.playbook_start_time))
        self.display_results()
