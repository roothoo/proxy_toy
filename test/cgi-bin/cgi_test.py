import cgi
import cgitb

form = cgi.FieldStorage()
first = form.getvalue('first')
second = form.getvalue('second')

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

print "<TITLE>CGI script output</TITLE>"
print "<H1>This is my first CGI script</H1>"
print "Hello, world!"
print "<br>"

print "first={0} second={1}".format(first, second)