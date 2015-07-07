import copy

from g_runner import interfaces

interfaces.Path.register(list)
interfaces.Path.register(tuple)
interfaces.Path.register(str)

class Tracker(interfaces.Tracker):
  """A tracker implementation tailored for the internals of the runner."""

  def __init__(self, original_tracker=None, deepcopy_memo=None):
    if original_tracker is not None:
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

  def add_path(self, path):
    self._paths.add(path)
    if path not in self._tasks_by_inputs:
      self._tasks_by_inputs[path] = set()
    if path not in self._tasks_by_outputs:
      self._tasks_by_outputs[path] = set()

  def remove_path(self, path):
    self._paths.remove(path)
    if path in self._tasks_by_inputs:
      del self._tasks_by_inputs[path]
    if path in self._tasks_by_outputs:
      del self._tasks_by_outputs[path]

  def add_task(self, task):
    self._tasks.add(task)
    for path in task.input_paths():
      self._tasks_by_inputs[path].add(task)
    for path in task.output_paths():
      self._tasks_by_outputs[path].add(task)

  def remove_task(self, task):
    self._tasks.remove(task)
    for path in task.input_paths():
      self._tasks_by_inputs[path].remove(task)
    for path in task.output_paths():
      self._tasks_by_outputs[path].remove(task)
    for (tag, tasks) in self._tasks_by_tags.items():
      tasks.remove(task)

  def add_task_tag(self, task, tag):
    if tag is None:
      return
    self._tasks_by_tags[tag].add(task)

  def clear_task_tags(self, task):
    if tag is None:
      return
    for (tag, tasks) in self._tasks_by_tags.items():
      tasks.remove(task)

  def __eq__(self, other):
    return self._paths == other._paths and self._tasks == other._tasks

  def __hash__(self):
    return hash((self._paths, self._tasks))

  def __copy__(self):
    return Tracker(self)

  def __deepcopy__(self, memo):
    return Tracker(self, deepcopy_memo=memo)

