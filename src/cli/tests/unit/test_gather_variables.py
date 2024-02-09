import unittest
import cli.logics.gather_variables as gather_variables

# To-Do
class TestAddNumbersFunction(unittest.TestCase):
  def read_default_variabels(self):
    result = "abv"
    gather_variables.set_environment_variables
    self.assertEqual(result, 8)

if __name__ == '__main__':
    unittest.main()
