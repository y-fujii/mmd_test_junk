# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import math
import numpy.matlib


def translate( x ):
	m = numpy.eye( 4 )
	m[0:3, 3] = x
	return numpy.mat( m )

def scale( s ):
	m = numpy.matlib.eye( 4 )
	m[range(3), range(3)] = s
	return m

def rotate( axis, theta ):
	a0 = (axis + 1) % 3
	a1 = (axis + 2) % 3
	s = math.sin( theta )
	c = math.cos( theta )
	m = numpy.matlib.eye( 4 )
	m[a0, a0] = +c
	m[a0, a1] = -s
	m[a1, a0] = +s
	m[a1, a1] = +c
	return m


if __name__ == "__main__":
	print( translate( [ 1.0, 2.0, 3.0 ] ) )
	print( rotate( 0, math.pi / 4 ) )
	print( rotate( 1, math.pi / 4 ) )
	print( rotate( 2, math.pi / 4 ) )
