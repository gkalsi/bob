import sys; sys.path.append("../")
import bob

cpp_def = {
	'sources' : ['test.cpp'],
	'target'  : 'test',
}

cpp = bob.Resource(
	cmd = "g++ -Wall {0} -o {1}".format(
		" ".join(cpp_def['sources']),
		cpp_def['target']),
	sources = cpp_def['sources'],
	target  = cpp_def['target'],
	hashcheck = True
)

cpp.build()