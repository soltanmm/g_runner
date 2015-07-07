import collections

from g_runner import interfaces


class PathState(object):
  """Surface-accessible path states."""
  outdated = 'outdated'
  up_to_date = 'up_to_date'

class EventFlags(
    collections.namedtuple(
        'EventFlags', [
              'hint_local',
              'paths_state',
              'tasks_tags',
          ])):
  """Flags for individual events.

  This object should never be created directly by the user; instead, use
  EventBuilder.

  Attributes:
    hint_local (bool): whether or not this is a well-controlled local change and
      the tracker's task-world-runtime doesn't need to be stopped to update the
      tracker and its tasks.
    paths_state (object): what state the paths selected/regenerated are in
      (should normally come from `PathState`).
    tasks_tags (list): what tags the tasks selected/regenerated have; if None,
      no tag changes are applied.
  """
  def __new__(cls, hint_local=False, paths_state=PathState.up_to_date,
              tasks_tags=None):
    return super(EventFlags, cls).__new__(cls, hint_local, paths_state,
                                          tasks_tags)


class Event(
    collections.namedtuple(
      'Event', [
          'path_selector',
          'path_regenerator',
          'task_selector',
          'task_regenerator',
          'flags',
      ])):
  """An event for the runner to handle.

  Outlines such events as: tracker modification requests, obsolescence of a
  label's current state, etc. This object should never be created directly by
  the user; instead, use EventBuilder.

  Attributes:
    path_selector (callable): a callable accepting an `interfaces.Tracker`
      object and returning a sequence of paths in that tracker.
    path_regenerator (callable): a callable accepting an `interfaces.Tracker`
      and a sequence of paths returned by `path_selector` and returning a new
      sequence of paths with which the old paths will be replaced. If None,
      selected paths aren't regenerated (are maintained).
    task_selector (callable): a callable accepting an `interfaces.Tracker`
      object and returning a sequence of tasks in that tracker.
    task_regenerator (callable): a callable accepting an `interfaces.Tracker`
      and a sequence of tasks returned by `task_selector` and returning a new
      sequence of tasks with which the old tasks will be replaced. If None,
      selected paths aren't regenerated (ar maintained).
    flags (EventFlags): ...
  """
  def __new__(cls, path_selector=None, path_regenerator=None,
              task_selector=None, task_regenerator=None, flags=EventFlags()):
    return super(Event, cls).__new__(cls, path_selector, path_regenerator,
                                     task_selector, task_regenerator, flags)
