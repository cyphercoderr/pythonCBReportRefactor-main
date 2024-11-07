import unittest
import sqlite3
from cb_sample import execute_query_with_date_range

class TestExecuteQueryWithDateRange(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for testing
        self.conn = sqlite3.connect(":memory:")
        self.cur = self.conn.cursor()

        # Create a test table and insert sample data
        self.cur.execute('''CREATE TABLE test_data (id INTEGER PRIMARY KEY, name TEXT, created_at DATE)''')
        self.cur.execute('''INSERT INTO test_data (name, created_at) VALUES (?, ?)''', ("User1", "2023-09-20"))
        self.cur.execute('''INSERT INTO test_data (name, created_at) VALUES (?, ?)''', ("User2", "2023-09-20"))
        self.cur.execute('''INSERT INTO test_data (name, created_at) VALUES (?, ?)''', ("User3", "2023-09-20"))
        self.conn.commit()

    def tearDown(self):
        # Close the database connection
        self.conn.close()

    def test_query_with_date_range(self):
        # Test with a date range of 7 days
        result = execute_query_with_date_range(self.cur, "SELECT name FROM test_data WHERE julianday('now') - julianday(created_at) < date_range", ["name"], 7)
        self.assertEqual(result, [("User1", ), ("User2", ), ("User3", )])

        # Test with a date range of 3 days
        result = execute_query_with_date_range(self.cur, "SELECT name FROM test_data WHERE julianday('now') - julianday(created_at) < date_range", ["name"], 3)
        self.assertEqual(result, [("User1", ), ("User2", ), ("User3", )])

        # Test with a date range of 1 day
        result = execute_query_with_date_range(self.cur, "SELECT name FROM test_data WHERE julianday('now') - julianday(created_at) < date_range", ["name"], 1)
        self.assertEqual(result, [("User1", ), ("User2", ), ("User3", )])

        # Test with no date range
        result = execute_query_with_date_range(self.cur, "SELECT name FROM test_data", ["name"], 0)
        self.assertEqual(result, [("User1", ), ("User2", ), ("User3", )])

if __name__ == '__main__':
    unittest.main()
