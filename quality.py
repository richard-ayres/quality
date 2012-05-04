# import coverage
# import nose
import ast
import inspect # remove me
import subprocess
import os.path
import sys

# maybe this isn't a good idea: this implementation inspects the code under test via
# the live objects in its module, post-import.  Maybe it'd be better to use python's
# source code tools?

IGNORED_ATTRS = [
	'im_self',
	'im_class',
	'im_func',
	'__func__',
]

def enumerate_module(modname):
	mod = __import__(modname)
	return enumerate_code(mod)

def enumerate_code(obj):
	ret = {}
	for name, member in inspect.getmembers(obj, lambda x: (inspect.isroutine(x) or inspect.isclass(x)) and not inspect.isbuiltin(x)):
		if name in IGNORED_ATTRS:
			# this attr is part of the data model; ignore it
			continue
		try:
			sourcefile = inspect.getsourcefile(member)
			sourcelines = inspect.getsourcelines(member)
		except TypeError:
			# this is a built-in class, usually part of the type system; inspect.isbuiltin doesn't exclude these
			# skip this item
			continue
		lines = inspect.getsourcelines(member)
		subs = enumerate_code(member)
		linenums = frozenset(range(lines[1], lines[1]+len(lines[0]))) - union_line_nums(subs)

		ret[name] = (member, list(linenums), subs)
	
	return ret

def union_line_nums(subs):
	ret = set()
	for sub in subs.itervalues():
		ret.update(sub[1])

		# gather line numbers from all sub-routines
		ret.update(union_line_nums(sub[2]))
	
	return ret

def quality(src_path, test_path):
	#1: cleanup from past runs
	subprocess.call(['coverage', 'erase'])

	#2: run unit tests with coverage
	# currently using shell to avoid infinite recursion when running quality under its own tests
	# fixme: run nose programmatically while avoiding the infinite recursion
	subprocess.call(['nosetests', '--with-coverage', test_path])

	#3: collect coverage XML
	# fixme: once nose is running in the same interpreter, just use the coverage API
	subprocess.call(['coverage', 'xml'])
	lxml.objectify.parse('coverage.xml')

	#4: enumerate code in module under test
	# add code under test to sys.path
	# todo: should this be a context manager instead?
	sys.path.append(os.path.dirname(src_path))
	# enumerate callables
	callables = enumerate_callables(os.path.splitext(os.path.basename(src_path))[0])
	# remove last entry from sys.path
	sys.path.pop()

	ret = {}
	for name, member in callables.iteritems():
		# for each callable...
		pass
		#5: calculate coverage for callables

		#6: analyze complexity
		#7: calculate quality

	return ret
