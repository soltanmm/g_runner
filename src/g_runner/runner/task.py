import copy

from g_runner import interfaces


class Task(interfaces.Task):

  def __init__(self, input_paths, output_paths, target, args=(), kwargs={}):
    self.input_paths = tuple(input_paths)
    self.output_paths = tuple(output_paths)
    self.target = target
    self.args = args
    self.kwargs = kwargs

  def input_paths(self):
    return self.input_paths

  def output_paths(self):
    return self.output_paths

  def run(self):
    return self.run(*self.args, **self.kwargs)

  def __eq__(self, other):
    return self.__dict__ == other.__dict__

  def __hash__(self):
    return hash((self.input_paths, self.output_paths, self.target, self.args,
                 frozenset(self.kwargs.items())))

  def __copy__(self):
    return Task(copy.copy(self.input_paths), copy.copy(self.output_paths),
                copy.copy(self.target), copy.copy(self.args),
                copy.copy(self.kwargs))

  def __deepcopy__(self, memo):
    return Task(
        copy.deepcopy(self.input_paths, memo),
        copy.deepcopy(self.output_paths, memo),
        copy.deepcopy(self.target, memo), copy.deepcopy(self.args, memo),
        copy.deepcopy(self.kwargs, memo))

