from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule  # noqa
from datetime import datetime  # noqa


class CallbackModule(DefaultCallbackModule):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'vanko'

    def __init__(self):
        super(CallbackModule, self).__init__()
        display_orig = self._display.display

        def display(msg, *args, **kwargs):
            msg = msg.strip()
            if msg.endswith('***'):
                stamp = str(datetime.now().replace(microsecond=0))
                if self._display.verbosity < 1:
                    stamp = stamp.split()[1]  # omit date part
                msg = '[%s] %s' % (stamp, msg)
            if msg:
                display_orig(msg, *args, **kwargs)

        self._display.display = display

    @property
    def _is_verbose(self):
        return self._display.verbosity > 1

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self._is_verbose or task.action != 'include':
            super(CallbackModule, self).v2_playbook_on_task_start(task, is_conditional)

    def v2_runner_on_skipped(self, result):
        if self._is_verbose:
            super(CallbackModule, self).v2_runner_on_skipped(result)

    def v2_runner_item_on_skipped(self, result):
        if self._is_verbose:
            super(CallbackModule, self).v2_runner_item_on_skipped(result)

    def v2_playbook_on_include(self, included_file):
        if self._is_verbose:
            super(CallbackModule, self).v2_playbook_on_include(included_file)
