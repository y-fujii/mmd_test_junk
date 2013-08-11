# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import math
import numpy


def conj( x ):
	r = numpy.empty_like( x )
	r[0 ] =  x[0 ]
	r[1:] = -x[1:]
	return r

def mul( x, y ):
	r = numpy.empty_like( x, dtype = numpy.result_type( x, y ) )
	r[0] = x[0] * y[0] - x[1] * y[1] - x[2] * y[2] - x[3] * y[3]
	r[1] = x[0] * y[1] + x[1] * y[0] + x[2] * y[3] - x[3] * y[2]
	r[2] = x[0] * y[2] - x[1] * y[3] + x[2] * y[0] + x[3] * y[1]
	r[3] = x[0] * y[3] + x[1] * y[2] - x[2] * y[1] + x[3] * y[0]
	return r

def inv( x ):
	return conj( x ) / numpy.dot( x, x )

def div( x, y ):
	return mul( x, conj( y ) ) / numpy.dot( y, y )

def matrix4( x ):
	x00 = x[0] * x[0]
	x01 = x[0] * x[1]
	x02 = x[0] * x[2]
	x03 = x[0] * x[3]
	x11 = x[1] * x[1]
	x12 = x[1] * x[2]
	x13 = x[1] * x[3]
	x22 = x[2] * x[2]
	x23 = x[2] * x[3]
	x33 = x[3] * x[3]
	return numpy.array( [
		[ x00 + x11 - x22 - x33, 2.0 * (x12 - x03),     2.0 * (x13 + x02),     0.0 ],
		[ 2.0 * (x12 + x03),     x00 - x11 + x22 - x33, 2.0 * (x23 - x01),     0.0 ],
		[ 2.0 * (x13 - x02),     2.0 * (x23 + x01),     x00 - x11 - x22 + x33, 0.0 ],
		[ 0.0,                   0.0,                   0.0,                   1.0 ],
	], dtype = x.dtype )

def transform( q, x ):
	#r = numpy.zeros( (4,), dtype = x.dtype )
	#r[1:] = x
	#return mul( mul( q, r ), conj( q ) )[1:]

	r0 = q[2] * x[2] - q[3] * x[1] + q[0] * x[0]
	r1 = q[3] * x[0] - q[1] * x[2] + q[0] * x[1]
	r2 = q[1] * x[1] - q[2] * x[0] + q[0] * x[2]

	s = numpy.empty_like( x )
	s[0] = (q[2] * r2 - q[3] * r1) * 2.0 + x[0]
	s[1] = (q[3] * r0 - q[1] * r2) * 2.0 + x[1]
	s[2] = (q[1] * r1 - q[2] * r0) * 2.0 + x[2]
	return s

def rotation( axis, theta ):
	c = math.cos( theta * 0.5 )
	s = math.sin( theta * 0.5 )
	n = math.sqrt( sum( t * t for t in axis ) )
	return numpy.array( [ c * n, axis[0] * s, axis[1] * s, axis[2] * s ] )

def from_float( x, dtype ):
	r = numpy.zeros( (4,), dtype = dtype )
	r[0] = x
	return r

def quaternion( src ):
	if isinstance( src, float ):
		r = from_float( src, numpy.float64 )
	elif isinstance( src, complex ):
		r = numpy.zeros( (4,), dtype = numpy.float64 )
		r[0] = src.real
		r[1] = src.imag
	elif isinstance( src, (numpy.ndarray, list) ):
		r = numpy.array( src )
		if r.shape != (4,):
			raise ValueError()
	else:
		raise ValueError()

	return Quaternion( r )


class Quaternion( object ):

	__slots__ = [ "_data" ]

	def __init__( self, data ):
		assert type( data ) is numpy.ndarray
		self._data = data

	def __str__( self ):
		return str( self._data )

	def __repr__( self ):
		return "Quaternion(%s)" % repr( list( self._data ) )

	def __iter__( self ):
		return iter( self._data )

	def __pos__( self ):
		return Quaternion( +self._data )

	def __neg__( self ):
		return Quaternion( -self._data )

	def __add__( lhs, rhs ):
		if isinstance( rhs, float ):
			return Quaternion( lhs._data + from_float( rhs, lhs._data.dtype ) )
		elif isinstance( rhs, Quaternion ):
			return Quaternion( lhs._data + rhs._data )
		else:
			return NotImplemented
	
	def __radd__( lhs, rhs ):
		if isinstance( lhs, float ):
			return Quaternion( from_float( rhs, lhs._data.dtype ) + rhs._data )
		elif isinstance( rhs, Quaternion ):
			return Quaternion( lhs._data + rhs._data )
		else:
			return NotImplemented

	def __sub__( lhs, rhs ):
		if isinstance( rhs, float ):
			return Quaternion( lhs._data - from_float( rhs, lhs._data.dtype ) )
		elif isinstance( rhs, Quaternion ):
			return Quaternion( lhs._data - rhs._data )
		else:
			return NotImplemented
	
	def __rsub__( lhs, rhs ):
		if isinstance( lhs, float ):
			return Quaternion( from_float( lhs, rhs._data.dtype ) - rhs._data )
		elif isinstance( rhs, Quaternion ):
			return Quaternion( lhs._data - rhs._data )
		else:
			return NotImplemented

	def __mul__( lhs, rhs ):
		if isinstance( rhs, float ):
			return Quaternion( lhs._data * rhs )
		elif isinstance( rhs, Quaternion ):
			return Quaternion( mul( lhs._data, rhs._data ) )
		else:
			return NotImplemented

	def __rmul__( lhs, rhs ):
		if isinstance( lhs, float ):
			return Quaternion( lhs * rhs._data )
		elif isinstance( lhs, Quaternion ):
			return Quaternion( mul( lhs._data, rhs._data ) )
		else:
			return NotImplemented

	def __div__( lhs, rhs ):
		if isinstance( rhs, float ):
			return Quaternion( lhs._data / rhs )
		elif isinstance( rhs, Quaternion ):
			return Quaternion( div( lhs._data, rhs._data ) )
		else:
			return NotImplemented

	def __rdiv__( rhs, lhs ):
		if isinstance( lhs, float ):
			return Quaternion( lhs * inv( rhs._data ) )
		elif isinstance( lhs, Quaternion ):
			return Quaternion( div( lhs._data, rhs._data ) )
		else:
			return NotImplemented

	def conj( self ):
		return Quaternion( conj( self._data ) )
	
	def norm2( self ):
		return numpy.dot( self._data, self._data )

	def norm1( self ):
		return math.sqrt( self.norm2() )

	def matrix4( self ):
		return matrix4( self._data )

	def array( self ):
		return self._data


if __name__ == "__main__":
	q = quaternion( [0.1, 0.2, 0.3, -0.4] )
	r = quaternion( [0.5, 0.6, -0.7, 0.8] )
	print( q + r - q - r )
	print( q / 1.0 - q )
	print( 1.0 / q * q - 1.0 )
	print( q * 2.0 - q - q )
	print( q / r * r / q - 1.0 )
	print( matrix4( rotation( [1.0, 0.0, 0.0], math.pi / 4.0 ) ) )
	print( matrix4( rotation( [0.0, 1.0, 0.0], math.pi / 4.0 ) ) )
	print( matrix4( rotation( [0.0, 0.0, 1.0], math.pi / 4.0 ) ) )
	print( transform(
		rotation( [0.0, 0.0, 1.0], math.pi / 4.0 ),
		numpy.array( [ 1.0, 0.0, 0.0 ] )
	) )
