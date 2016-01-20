import cgi
import cgitb

cgitb.enable()

form = cgi.FieldStorage()
upload_file = form['filename']

message = ''
if upload_file.filename:
    message = upload_file.file.read()

print """\
Content-Type: text/html\n
<html>
<body>
   <p>%s</p>
</body>
</html>
""" % (message,)