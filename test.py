import unittest
import json
from app import app

app.testing = True

class TestCase(unittest.TestCase):

    def test_home(self):
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_request(self):
        tester = app.test_client(self)
        response = tester.get('/Request', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_plot(self):
        with app.test_client() as client:
            # send data as POST form to endpoint
            sent = {'return_url': 'my_test_url'}
            result = client.post('/Plot', data=sent)
            # check result from server with expected data
            self.assertEqual(result.data, json.dumps(sent))

    def test_world_map(self):
        tester = app.test_client(self)
        response = tester.get('/World_Map', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_top_death(self):
        tester = app.test_client(self)
        response = tester.get('/Top_Deaths', content_type='html/text')
        self.assertEqual(response.status_code, 200)

    def test_top_affected(self):
        tester = app.test_client(self)
        response = tester.get('/Top_Affected', content_type='html/text')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
