import simplejson as json
from buildbot.worker import Worker

### Fetch workers from json file
Workers  = []
WorkerTags = {}

for worker in json.load(open('../workers.json')):
	tags = worker.pop('tags', ['default'])
	name = worker.pop('name')

	for tag in tags:
		if tag not in WorkerTags:
			WorkerTags[tag] = []
		WorkerTags[tag].append(name)

	Workers.append(Worker(name, worker.pop('pass'), **worker))