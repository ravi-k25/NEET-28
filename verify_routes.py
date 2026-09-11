from app import app

print(app.url_map)
client = app.test_client()
paths = ['/', '/tasks', '/timer', '/analytics', '/tests', '/syllabus', '/mistakes']
for path in paths:
    response = client.get(path)
    print(path, response.status_code)
