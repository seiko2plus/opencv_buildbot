#!/usr/bin/env python3
import sys
sys.path.append('/app/pysrc')
print('Attach to debugger...')

import os
import pydevd
if os.environ.get('DEBUG_HOST', None) == '':
  del os.environ['DEBUG_HOST']
if os.environ.get('DEBUG_PORT', None) == '':
  del os.environ['DEBUG_PORT']

pydevd.settrace(
	os.environ.get('DEBUG_HOST', '127.0.0.1'),
	port=int(os.environ.get('DEBUG_PORT', '5678')),
	stdoutToServer=True, stderrToServer=True,
	suspend=True, trace_only_current_thread=False
)

from buildbot.scripts import runner
runner.run()
