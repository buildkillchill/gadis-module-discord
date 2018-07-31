import socket
import sys
import uncompyle6
from io import StringIO
f = StringIO()
if not os.path.exists(os.path.expanduser("~/.gadis")):
	uncompyle6.uncompyle_file('~/.gadis/share/gadis/settings.pyc', f)
else:
	uncompyle6.uncompyle_file('/usr/local/share/gadis/settings.pyc', f)
f.seek(0)
exec(f.read(), globals(), locals())
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
addr = ('127.0.0.1', Settings.Remote["port"])
sock.connect(addr)

cmd = sys.argv[1]
args = sys.argv[2:]

if cmd == "send":
	chan = sys.argv[2]
	msg = " ".join(sys.argv[3:])
	msg = "msg {} {}".format(chan, msg)
	sock.send(msg.encode('utf-8'))
elif cmd == "shutdown":
	sock.send("shutdown".encode('utf-8'))
elif cmd == "noadmin":
	sock.send("noadmin {}".format(args[0]).encode('utf-8'))

sock.close()
