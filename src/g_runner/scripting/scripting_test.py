import unittest

from g_runner import scripting

class ScriptingTest(unittest.TestCase):

  def test_scripted_run_by_identifiers(self):
    builder = scripting.TrackerBuilder()
    state = [0 for i in range(3)]

    @builder.task()
    def task0():
      state[0] = state[0] + 1

    @builder.task()
    def task1():
      state[1] = state[1] + 1

    @builder.task(input_paths=(task0, task1))
    def task2():
      self.assertEqual(1, state[0])
      self.assertEqual(1, state[1])
      state[2] = state[2] + 1

    builder.run(outdated=True)

    for state_element in state:
      self.assertEqual(1, state_element)

