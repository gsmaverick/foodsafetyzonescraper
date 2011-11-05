#!c:/Python27/python.exe -u

import simplejson as json

# All reports will be added into this list
a = []

for i in range(0, 166):
	f = open('results/11_5_2011_' + str(i) + '.json', 'r')
	_f = json.loads(f.read())
	a.extend(_f)
	f.close()

f = open('11_5_2011.json', 'w')
f.write(json.dumps(a, sort_keys=True))
f.close()