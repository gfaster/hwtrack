## HW Track

this is a little program I wrote so that I can easily add assignments to Things 3


## MOTIVATION
Things 3 is an IOS / MacOS exclusive app, and I spend most of my day at my Windows machine. I wanted to be able to quickly add an assignment that is then added to Things 3 at the end of the school day.

## HOW IT WORKS
When the program is ran using the `add` argument, the user is prompted for the title of the to-do, notes for it, and the class that it is for. The todo is then added to a SQLite database. At the end of the school day, Task Scheduler runs the program with the `open_connection` argument and a TCP server is started at port `8000`. At the same time, my Ipad sends a GET request to the newly opened server and the server returns JSON according to the Things 3 JSON specifications. Once the project for the day is added on my Ipad, it sends a request to mark off the tasks as done in the SQLite database and to shutdown the server

## TODO
`[ ]` properly shut down the server instead of just sending an interrupt signal to the main PID
`[ ]` don't return json if no tasks were added during the day 