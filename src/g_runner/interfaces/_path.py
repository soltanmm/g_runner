import abc


class Path(object):
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __iter__(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def __len__(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def __eq__(self, other):
    raise NotImplementedError()

  @abc.abstractmethod
  def __hash__(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def __copy__(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def __deepcopy__(self, memo):
    raise NotImplementedError()
