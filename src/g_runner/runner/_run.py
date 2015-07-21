import collections
import copy
import itertools
import os
import threading

from g_runner import interfaces
from g_runner.runner import _event
from g_runner.runner import tracker as _tracker


class RunnerError(Exception):

  def __init__(self, exceptions_iterable):
    super(RunnerError, self).__init__('Some exception(s) were raised')
    self.exceptions = list(exceptions_iterable)


class _PathState(_event.PathState):
  """State of a path during a run.

  Extends _event.PathState with an intermediary state `updating`, representing a
  path that is being output by some running task, and `updated`, representing a
  path that has finished being output and is a candidate for being considered
  `up_to_date`. `poisoned` means that it's `outdated` and we cannot bring it
  `up_to_date` (e.g. because the task to bring it up to date failed)."""
  updating = 'updating'
  updated = 'updated'
  poisoned = 'poisoned'


class _TaskState(object):
  """State of a task during a run."""
  stopped = 'stopped'
  running = 'running'

  # The task is running but we want to remove it
  zombie = 'zombie'


class RunnerCallbacks(object):
  """Callbacks during a run of tracked tasks.

  Useful for verbose output of the run state. Note that callbacks have no
  explicit locking from the runner, thus thread safety must be ensured by the
  callee."""

  def on_task_running(self, tracker, task):
    """Called when a task enters the running state."""
    pass

  def on_task_stopped(self, tracker, task):
    """Called when a task enters the stopped state."""
    pass

  def on_task_failed(self, tracker, task):
    """Called when a task failed.

    Note that this is a refinement of a task stopping; it is called in addition
    to on_task_stopped."""
    pass

  def on_path_added(self, tracker, path):
    """Called when a path is added to the tracker."""
    pass

  def on_path_outdated(self, tracker, path):
    """Called when a path enters the outdated state."""
    pass

  def on_path_updating(self, tracker, path):
    """Called when a path enters the updating state."""
    pass

  def on_path_up_to_date(self, tracker, path):
    """Called when a path enters the up-to-date state."""
    pass

  def on_event(self, tracker, event):
    """Called when the runner processes an event."""
    pass

def _run_tracker_poll_event_iterator(event_iterator, out_event_deque):
  for event in event_iterator:
    out_event_deque.append(event)


class _TrackerRunner(object):

  def __init__(self, tracker, outdated=True, callbacks=RunnerCallbacks(),
               keep_going=False):
    if not isinstance(callbacks, RunnerCallbacks):
      raise TypeError('expected `callbacks` to be a `RunnerCallbacks`')
    self.tracker = _tracker.Tracker(tracker)
    if outdated:
      self.path_states = dict(
          (path, _PathState.outdated) for path in tracker.paths())
      self.paths_by_state = {
          _PathState.outdated: set(tracker.paths()),
          _PathState.updating: set(),
          _PathState.up_to_date: set(),
          _PathState.poisoned: set()
      }
    else:
      self.path_states = dict(
          (path, _PathState.up_to_date) for path in tracker.paths())
      self.paths_by_state = {
          _PathState.outdated: set(),
          _PathState.updating: set(),
          _PathState.up_to_date: set(tracker.paths()),
      }

    self.task_states = dict(
        (task, _TaskState.stopped) for task in tracker.tasks())
    self.tasks_by_state = {
        _TaskState.stopped: set(tracker.tasks()),
        _TaskState.running: set(),
    }
    self.task_generated_events = {}
    self.callbacks = callbacks
    self.keep_going = keep_going
    self.failures_deque = []
    self.lock = threading.RLock()

  def _remove_path(self, path):
    with self.lock:
      self.tracker = self.tracker.replaced(old_paths=[path])
      self.paths_by_state[self.path_states[path]].remove(path)
      del self.path_states[path]

  def _add_path(self, path, state):
    with self.lock:
      self.tracker = self.tracker.replaced(new_paths=[path])
      self.paths_by_state[state].add(path)
      self.path_states[path] = state
    self.callbacks.on_path_added(self.tracker, path)
    if state == _PathState.outdated:
      self.callbacks.on_path_outdated(self.tracker, path)
    elif state == _PathState.up_to_date:
      self.callbacks.on_path_up_to_date(self.tracker, path)
    # note that there's no case where a path can be added in the 'updating'
    # state.

  def _remove_task(self, task):
    """Remove a task.

    If we're running the task currently, its status is updated to 'zombie'."""
    with self.lock:
      if self.task_states[task] == _TaskState.running:
        self._set_task_state(task, _TaskState.zombie)
      elif self.task_states[task] == _TaskState.zombie:
        # don't need to do anything
        pass
      else:
        self.tracker = self.tracker.replaced(old_tasks=[task])
        self.tasks_by_state[self.task_states[task]].remove(task)
        del self.task_states[task]

  def _add_task(self, task):
    with self.lock:
      self.tracker = self.tracker.replaced(new_tasks=[task])
      self.task_states[task] = _TaskState.stopped
      self.tasks_by_state[_TaskState.stopped].add(task)

  def _set_path_state(self, path, state):
    with self.lock:
      self.paths_by_state[self.path_states[path]].discard(path)
      self.path_states[path] = state
      self.paths_by_state[state].add(path)
    if state == _PathState.outdated:
      self.callbacks.on_path_outdated(self.tracker, path)
    elif state == _PathState.updating:
      self.callbacks.on_path_updating(self.tracker, path)
    elif state == _PathState.up_to_date:
      self.callbacks.on_path_up_to_date(self.tracker, path)

  def _set_task_state(self, task, state):
    with self.lock:
      self.tasks_by_state[self.task_states[task]].discard(task)
      self.task_states[task] = state
      self.tasks_by_state[state].add(task)
    if state == _TaskState.stopped:
      self.callbacks.on_task_stopped(self.tracker, task)
    elif state == _TaskState.running:
      self.callbacks.on_task_running(self.tracker, task)

  def _replace_task_tags(self, task, tags):
    with self.lock:
      self.tracker = self.tracker.replaced(
          old_tasks=[task],
          new_tagged_tasks={task:tags})

  def _handle_events(self, events):
    """Applies the events.

    Note: does not handle the events beyond applying them, e.g. does not run
    tasks for newly outdated paths. Not thread safe.

    Returns:
      A list of valid yet unhandled events. These should be passed back in to
      the function at a later point."""
    with self.lock:
      for event in events:
        self.callbacks.on_event(self.tracker, event)
        if event.path_selector is not None:
          paths = set(event.path_selector(self.tracker))
          if event.path_regenerator is not None:
            new_paths = set(event.path_regenerator(self.tracker, paths))
            # replace paths with new_paths both in the tracker and in this scope
            removed_paths = paths.difference(new_paths)
            new_new_paths = new_paths.difference(paths)
            for path in removed_paths:
              self._remove_path(path)
            for path in new_new_paths:
              self._add_path(path, event.flags.paths_state)
            paths = new_paths
          # Note that we only allow transitions to the 'updated' from
          # 'updating', in which case we consider the state transition as being
          # from 'updating' to `up_to_date`, else it's a reset to 'outdated'.
          if event.flags.paths_state == _PathState.updated:
            for path in paths:
              if self.path_states[path] == _PathState.updating:
                self._set_path_state(path, _PathState.up_to_date)
              else:
                self._set_path_state(path, _PathState.outdated)
          else:
            for path in paths:
              self._set_path_state(path, event.flags.paths_state)
        if event.task_selector is not None:
          tasks = set(event.task_selector(self.tracker))
          if event.task_regenerator is not None:
            new_tasks = set(event.task_regenerator(self.tracker, tasks))
            removed_tasks = tasks.difference(new_tasks)
            new_new_tasks = new_tasks.difference(tasks)
            for task in removed_tasks:
              self._remove_task(task)
              if event.flags.removed_tasks_outdate_paths:
                for path in task.output_paths():
                  self._set_path_state(path, _PathState.outdated)
            for task in new_new_tasks:
              self._add_task(task)
            tasks = new_tasks
          if event.flags.tasks_tags is not None:
            for task in tasks:
              self._replace_task_tags(task, event.flags.tasks_tags)
    return []

  def _run_task_handle_updated_event(self, task, event_deque):
    with self.lock:
      self._set_task_state(task, _TaskState.running)
    successful = False
    try:
      task.run()
      successful = True
    except Exception as e:
      self.callbacks.on_task_failed(self.tracker, task)
      self.failures_deque.append(e)
    # the deque structure doesn't need locking! woo!
    if successful:
      event_deque.append(
          _event.Event(
              path_selector=lambda ignored_tracker: task.output_paths(),
              flags=_event.EventFlags(
                  hint_local=True,
                  paths_state=_PathState.updated)
          ))
    else:
      event_deque.append(
          _event.Event(
              path_selector=lambda ignored_tracker: task.output_paths(),
              flags=_event.EventFlags(
                  hint_local=True,
                  paths_state=_PathState.poisoned)
          ))
    with self.lock:
      if self.task_states[task] == _TaskState.zombie:
        self._remove_task(task)
      else:
        self._set_task_state(task, _TaskState.stopped)

  def _dispatch_task(self, task, event_deque):
    event_deque.append(
        _event.Event(
            path_selector=lambda ignored_tracker: task.output_paths(),
            flags=_event.EventFlags(
                hint_local=True,
                paths_state=_PathState.updating)
        ))
    threading.Thread(
        target=self._run_task_handle_updated_event,
        args=(task, event_deque)
    ).start()

  def _run_update(self, event_deque):
    """Begin running a round of tasks to update paths."""
    available_tasks = set(self.tasks_by_state[_TaskState.stopped])
    available_paths = set(self.paths_by_state[_PathState.outdated])
    nixed_paths = set()
    for path in available_paths:
      if path not in nixed_paths:
        for task in available_tasks:
          if path in task.output_paths() and reduce(
              lambda a, b: a and b,
              (self.path_states[input_path] == _PathState.up_to_date
               for input_path in task.input_paths()), True):
            # if we are here then we know that this task updates the outdated
            # path and all of its inputs are up to date.
            nixed_paths.update(set(task.output_paths()))
            self._dispatch_task(task, event_deque)

  def _up_to_date(self):
    return reduce(
        lambda a, b: a and b,
        (state == _PathState.up_to_date or state == _PathState.poisoned
         for state in self.path_states.values()), True)

  def run(self, runner_event_iterator):
    """Run the passed tracker.

    Runs until all tracked tasks are completed and all events have been
    processed.  While cycles cannot be directly expressed in the tracker and
    handled from the tracker, the `task_event_generator` can outmode paths per
    task and thus simulate a cycle between paths over tasks.

    Arguments:
      tracker (interfaces.Tracker): ...
      runner_event_iterator (iterator): an iterator over Event objects. Note
        that the tracker's tasks will continue to run as long as this iterator
        is live.
    """
    runner_event_deque = collections.deque()
    runner_event_poll_thread = threading.Thread(
        target=_run_tracker_poll_event_iterator,
        args=(runner_event_iterator, runner_event_deque))
    runner_event_poll_thread.start()
    runner_events = []

    # Pump the queue's initial events
    while True:
      try:
        runner_events.append(runner_event_deque.popleft())
      except:
        break

    while (runner_event_poll_thread.is_alive() or len(runner_events) > 0 or
           not self._up_to_date()):
      if len(self.failures_deque) > 0 and not self.keep_going:
        raise RunnerError(self.failures_deque)
      # Pump the queue
      while True:
        try:
          runner_events.append(runner_event_deque.popleft())
        except:
          break
      runner_events = self._handle_events(runner_events)
      # Now run the tasks that we know to affect targets that are out of date.
      # We do not directly support multiple tasks producing the same path; that
      # has to be handled a layer above us via user event generators (and really
      # only for cycle-inducing tasks).
      self._run_update(runner_event_deque)

    if len(self.failures_deque) > 0:
      raise RunnerError(self.failures_deque)


def run_tracker(tracker, runner_event_iterator, outdated=False,
                keep_going=False, callbacks=RunnerCallbacks()):
  tracker_runner = _TrackerRunner(
      tracker, outdated=outdated, keep_going=keep_going, callbacks=callbacks)
  return tracker_runner.run(runner_event_iterator)
