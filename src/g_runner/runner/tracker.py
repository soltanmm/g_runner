import copy
import itertools

from g_runner import interfaces

interfaces.Path.register(list)
interfaces.Path.register(tuple)
interfaces.Path.register(str)

def is_tracker_valid(tracker):
  return len(set(tracker.paths())) == len(tracker.paths()) and reduce(
          lambda a, b: a and b,
          [path in tracker.paths()
           for task in tracker.tasks()
           for path in itertools.chain(task.input_paths(),
                                       task.output_paths())],
          True)


class Tracker(interfaces.Tracker):
  """A tracker implementation tailored for the internals of the runner."""

  def __init__(self, original_tracker=None, deepcopy_memo=None):
    if original_tracker is not None:
      if not isinstance(original_tracker, interfaces.Tracker):
        raise TypeError('expected tracker to be `interfaces.Tracker`')
      if not is_tracker_valid(original_tracker):
        raise ValueError('expected a valid tracker')
      if deepcopy_memo:
        self._paths = set(copy.deepcopy(path, deepcopy_memo)
                          for path in original_tracker.paths())
        self._tasks = set(copy.deepcopy(task, deepcopy_memo)
                          for task in original_tracker.tasks())
        self._tasks_by_tags = dict(
            (copy.deepcopy(tag, deepcopy_memo),
             copy.deepcopy(tasks, deepcopy_memo))
            for (tag, tasks) in original_tracker.tagged_tasks())
      else:
        self._paths = set(copy.copy(path) for path in original_tracker.paths())
        self._tasks = set(copy.copy(task) for task in original_tracker.tasks())
        self._tasks_by_tags = dict(
            (copy.copy(tag, deepcopy_memo),
             copy.copy(tasks, deepcopy_memo))
            for (tag, tasks) in original_tracker.tagged_tasks())
      self._tasks_by_inputs = dict(
          (path, set(task for task in self._tasks
                     if path in list(task.input_paths())))
          for path in self._paths)
      self._tasks_by_outputs = dict(
          (path, set(task for task in self._tasks
                     if path in list(task.output_paths())))
          for path in self._paths)
    else:
      self._paths = set()
      self._tasks = set()
      self._tasks_by_inputs = {}
      self._tasks_by_outputs = {}
      self._tasks_by_tags = {}

  def tasks(self):
    return self._tasks

  def tasks_by_tags(self, tags):
    tasksets = list(set(self._tasks_by_tags[tag]) for tag in tags)
    if len(tasksets) < 1:
      return set()
    elif len(tasksets) < 2:
      return tasksets[0]
    else:
      taskset = tasksets[0].intersection(tasksets[1])
      for i in range(2, len(tasksets)):
        taskset = taskset.intersection(tasksets[i])
      return taskset

  def tagged_tasks(self):
    return self._tasks_by_tags.items()

  def tasks_by_outputs(self, output_paths):
    tasksets = list(set(self._tasks_by_outputs[path]) for path in output_paths)
    if len(tasksets) < 1:
      return set()
    elif len(tasksets) < 2:
      return tasksets[0]
    else:
      taskset = tasksets[0].intersection(tasksets[1])
      for i in range(2, len(tasksets)):
        taskset = taskset.intersection(tasksets[i])
      return taskset

  def tasks_by_inputs(self, input_paths):
    tasksets = list(set(self._tasks_by_inputs[path]) for path in input_paths)
    if len(tasksets) < 1:
      return set()
    elif len(tasksets) < 2:
      return tasksets[0]
    else:
      taskset = tasksets[0].intersection(tasksets[1])
      for i in range(2, len(tasksets)):
        taskset = taskset.intersection(tasksets[i])
      return taskset

  def paths(self):
    return self._paths

  def replaced(self, old_paths=set(), new_paths=set(),
               old_tasks=set(), new_tasks=set(), new_tagged_tasks=dict()):
    new_tracker = Tracker()
    new_tracker._paths = (
        self._paths.difference(set(old_paths)).union(set(new_paths)))
    new_tracker._tasks = (
        self._tasks.difference(set(old_tasks)).union(set(new_tasks).union(
            set(new_tagged_tasks.keys()))))
    new_tracker._tasks_by_tags = {}
    for (tag, tasks) in self._tasks_by_tags:
      taskset = set(task for task in tasks if task not in old_tasks)
      if len(taskset) > 0:
        new_tracker._tasks_by_tags[tag] = taskset
    for (task, tags) in new_tagged_tasks.items():
      for tag in tags:
        new_tracker._tasks_by_tags.setdefault(tag, set()).add(task)
    new_tracker._tasks_by_inputs = dict(
        (path, set(task for task in new_tracker._tasks
                   if path in list(task.input_paths())))
        for path in new_tracker._paths)
    new_tracker._tasks_by_outputs = dict(
        (path, set(task for task in new_tracker._tasks
                   if path in list(task.output_paths())))
        for path in new_tracker._paths)
    return new_tracker

  def __eq__(self, other):
    return self._paths == other._paths and self._tasks == other._tasks

  def __hash__(self):
    return hash((self._paths, self._tasks))

  def __copy__(self):
    return Tracker(self)

  def __deepcopy__(self, memo):
    return Tracker(self, deepcopy_memo=memo)


