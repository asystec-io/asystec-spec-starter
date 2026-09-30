import copy
import unittest
from report import build_report


class ReportTests(unittest.TestCase):
    def test_active_only_sorted_and_no_mutation(self):
        rows = [{'name':'Zulu','active':True},{'name':'Hidden','active':False},{'name':'Alpha','active':True}]
        before = copy.deepcopy(rows)
        self.assertEqual(build_report(rows), {'active_count':2,'names':['Alpha','Zulu']})
        self.assertEqual(rows, before)

    def test_empty(self):
        self.assertEqual(build_report([]), {'active_count':0,'names':[]})

    def test_invalid_input(self):
        for invalid in (None, {}, [{'name':'Alpha','active':'yes'}], [{'name':'','active':True}], [{'name':'Alpha'}]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build_report(invalid)


if __name__ == '__main__':
    unittest.main()
