LinuxCompilers = {}

def _env(cc, cxx, path):
	env = {}
	env['CC']  = "%s/%s" % (path, cc)
	env['CXX'] = "%s/%s" % (path, cxx)
	return env

def _getGCC(ver, path='/usr/lib/ccache'):
	nm = "gcc-%s" %ver
	return { nm: _env(nm, "g++-%s" %ver, path) }

def _getClang(ver, path='/usr/lib/ccache'):
	nm = "clang-%s" %ver
	return { nm: _env(nm + '.0', "clang++-%s.0" %ver, path)}

for gv in ['4.9', '5', '6', '7', '8']:
	LinuxCompilers.update(_getGCC(gv))

for cv in ['4', '5', '6']:
	LinuxCompilers.update(_getClang(cv))