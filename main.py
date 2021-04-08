import sys
import time
import datetime
import json
import sqlite3
import socketserver
from http.server import BaseHTTPRequestHandler
import threading, os, signal


class MyHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == '/hwlist':
			conn = create_connection("hwdb.db")
			todo_list = get_todos(conn)
			response_json = json.dumps(create_project_json(todo_list))

			self.send_response(200)
			self.send_header('Content-Type', 'application/json')
			self.end_headers()
			self.wfile.write(response_json.encode(encoding='utf_8'))

		elif self.path == '/shutdown':
			self.send_error(500)
			time.sleep(1)
			os.kill(os.getpid(), signal.SIGINT)

		elif self.path == '/complete':
			self.send_response(200)
			conn = create_connection("hwdb.db")
			todo_list = get_todos(conn, am_sending=True)
			self.send_header('Content-Type', 'application/text')
			self.end_headers()
			self.wfile.write("done".encode(encoding='utf_8'))


			




		else:
			self.send_response(404)

PORT = 8000

def main():
	pass

def tests():
	conn = create_connection("testdb.db")

	try:
		c = conn.cursor()
		c.execute("DROP TABLE todos")
		conn.commit()
	except:
		pass

	create_tables(conn)	

	testtodo = Todo("title", "notes go here", "math")

	add_todo(conn, testtodo)

	fetched = get_todos(conn)

	assert testtodo.to_json() == fetched[0].to_json(), "\n" + str(fetched[0].to_json()) + "\n" + str(testtodo.to_json())

	project = create_project_json(fetched)

	print(json.dumps(project, indent = 3))


	print("tests passed")



def add():
	title = input("item title: ")
	notes = input("notes: ")

	tag = ""
	while tag not in ("english", "math", "psych", "gym", "design", "chem"):
		tag = input("class: ")

	todo = Todo(title, notes, tag)

	conn = create_connection("hwdb.db")
	create_tables(conn)
	add_todo(conn, todo)

def prepare_send():
	handler = MyHandler
	with socketserver.TCPServer(("", PORT), handler) as httpd:
		print("serving at port", PORT)
		print(f"goto 127.0.0.1:{PORT}/hwlist")
		# print(f"goto 127.0.0.1:{PORT}/shutdown to shutdown")


		httpd.serve_forever()




class Todo(object):
	"""docstring for Todo"""
	def __init__(self, title, notes, tag, deadline=None, created=None):
		super(Todo, self).__init__()
		self.title = title
		self.notes = notes
		self.tag = tag
		assert tag in ("english", "math", "psych", "gym", "design", "chem"), tag
		
		if not created:
			self.created = datetime.datetime.now().isoformat()
		else: 
			self.created = created

		if not deadline:
			self.deadline = next_class(tag)
		else:
			self.deadline = deadline


	def fields(self):
		return self.title, self.notes, self.tag, self.deadline, self.created

	def days_until_due(self):
		td = datetime.datetime.strptime(self.deadline, "%Y-%m-%d").date() - datetime.date.today()
		return td.days

	def to_json(self):
		out = {
			"type": "to-do",
			"attributes": {
				"title": self.title,
				"notes": self.notes,
				"when": "today",
				"deadline": self.deadline

			}
		}
		return out

# get the date of the next class_name
def next_class(class_name):
	possible_names = ("english", "math", "psych", "gym", "design", "chem")
	assert class_name in possible_names

	classes = [
	("english", "psych", "gym", "design", "chem"),
	("math", "gym"),
	("english", "math", "psych", "gym", "design", "chem"),
	("english", "psych", "gym", "design", "chem"),
	("math", "gym"),
	tuple(),
	tuple()
	]

	# start searching from tomorrow
	check_date = (datetime.datetime.today().weekday() + 1) % 7
	days_ahead = 1

	# iterate until the day has class_name
	while class_name not in classes[check_date]:
		check_date = (check_date + 1) % 7
		days_ahead += 1


	return str(datetime.date.today() + datetime.timedelta(days_ahead))

def create_connection(db_file):
	""" create a database connection to the SQLite database
		specified by db_file
	:param db_file: database file
	:return: Connection object or None
	"""
	conn = None
	try:
		conn = sqlite3.connect(db_file)
		return conn
	except Exception as e:
		raise Exception(f"Connection creation error: {e}")

	return conn

def create_tables(conn):
	query = """ CREATE TABLE IF NOT EXISTS todos (
										id integer PRIMARY KEY,
										title text NOT NULL,
										notes text,
										tag text,
										deadline text,			
										created text,
										hassent int DEFAULT 0
									); """


	if conn is None:
		raise ("conn is None in table creation")

	c = conn.cursor()
	c.execute(query)
	conn.commit()

def add_todo(conn, todo:Todo):
	query  = '''INSERT INTO todos(title,notes,tag,deadline,created)
				VALUES(?,?,?,?,?) '''

	cur = conn.cursor()
	cur.execute(query, (todo.fields()))
	conn.commit()

	return cur.lastrowid

def update_sent(conn):
	query = '''UPDATE todos 
		SET hassent = 1
		WHERE hassent = 0;'''

	c = conn.cursor()
	c.execute(query)
	conn.commit()

def get_todos(conn, am_sending=False):

	query = "SELECT * FROM todos WHERE hassent = 0"
	c = conn.cursor()
	c.execute(query)
	rows = c.fetchall()

	# mark the rows we got so we don't send duplicates
	if am_sending:
		update_sent(conn)
	
	# convert the database entries to Todo objects
	out = []
	for row in rows:
		out.append(Todo(*row[1:-1]))

	return out

def create_project_json(todo_list):
	project_title = f"Homework for {str(datetime.date.today())}"
	if todo_list:
		
		due_date = str(datetime.date.today() + datetime.timedelta(max([item.days_until_due() for item in todo_list])))

		json_raw = [
		{
			"type": "project",
			"attributes": {
				"title": project_title,
				"area": "School",
				"when": "today",
				"deadline": due_date,
				"items": [item.to_json() for item in todo_list]
			}
		}
		]

	else:
		json_raw = [
		{
			"type": "project",
			"attributes": {
				"title": project_title,
				"area": "School",
				"when": "today",
				"notes": "nothing for today!",
				"completed": True
			}
		}
		]

	return json_raw


if __name__ == "__main__":
	if "test" in sys.argv:
		tests()
	elif "add" in sys.argv:
		add()
	elif "open_connection" in sys.argv:
		prepare_send()
	else:
		main()