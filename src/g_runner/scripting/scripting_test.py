import unittest

from g_runner import scripting

class ScriptingTest(unittest.TestCase):

  def setUp(self):
    self.builder = scripting.TrackerBuilder()

  def test_scripted_run_by_identifiers(self):
    state = [0 for i in range(3)]
    @self.builder.task()
    def task0():
      state[0] = state[0] + 1

    @self.builder.task()
    def task1():
      state[1] = state[1] + 1

    @self.builder.task(input_paths=(task0, task1))
    def task2():
      self.assertEqual(1, state[0])
      self.assertEqual(1, state[1])
      state[2] = state[2] + 1

    self.builder.run(outdated=True)

    for state_element in state:
      self.assertEqual(1, state_element)

