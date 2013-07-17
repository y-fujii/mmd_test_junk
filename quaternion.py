# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import collections
import math
import numpy


def conj( x ):
	return numpy.concatenate( [ x[:1], -x[1:] ] )

def mul( x, y ):
	return numpy.array( [
		x[0] * y[0] - x[1] * y[1] - x[2] * y[2] - x[3] * y[3],
		x[0] * y[1] + x[1] * y[0] + x[2] * y[3] - x[3] * y[2],
		x[0] * y[2] - x[1] * y[3] + x[2] * y[0] + x[3] * y[1],
		x[0] * y[3] + x[1] * y[2] - x[2] * y[1] + x[3] * y[0],
	] )

def div( x, y ):
	return mul( x, conj( y ) ) / numpy.sum( y * y )

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
	] )


# XXX
class Quaternion( object ):

	__slots__ = [ "_data" ]

	def __init__( self, src ):
		if isinstance( src, Quaternion ):
			self._data = numpy.array( src._data )
		elif isinstance( src, float ):
			self._data = numpy.array( [src, 0.0, 0.0, 0.0] )
		elif isinstance( src, complex ):
			self._data = numpy.array( [src.real, src.imag, 0.0, 0.0] )
		elif isinstance( src, collections.Iterable ):
			self._data = numpy.array( list( src ) )
			if self._data.shape != (4,):
				raise ValueError()
		else:
			raise ValueError()

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
		return Quaternion( lhs._data + Quaternion( rhs )._data )
	
	def __radd__( lhs, rhs ):
		return Quaternion( Quaternion( lhs._data ) + rhs._data )

	def __sub__( lhs, rhs ):
		return Quaternion( lhs._data - Quaternion( rhs )._data )
	
	def __rsub__( lhs, rhs ):
		return Quaternion( Quaternion( lhs._data ) - rhs._data )

	def __mul__( lhs, rhs ):
		return Quaternion( mul( lhs._data, Quaternion( rhs )._data ) )

	def __rmul__( lhs, rhs ):
		return Quaternion( mul( Quaternion( lhs )._data, rhs._data ) )

	def __div__( lhs, rhs ):
		return Quaternion( div( lhs._data, Quaternion( rhs )._data ) )

	def __rdiv__( rhs, lhs ):
		return Quaternion( div( Quaternion( lhs )._data, rhs._data ) )

	def conj( self ):
		return Quaternion( conj( self._data ) )
	
	def norm2( self ):
		return numpy.sum( self._data * self._data )

	def norm1( self ):
		return math.sqrt( self.norm2() )

	def matrix4( self ):
		return matrix4( self._data )

	def array( self ):
		return self._data


def rotation( axis, theta ):
	c = math.cos( theta * 0.5 )
	s = math.sin( theta * 0.5 )
	n = math.sqrt( sum( t * t for t in axis ) )
	return Quaternion( [ c * n, axis[0] * s, axis[1] * s, axis[2] * s ] )


if __name__ == "__main__":
	q = Quaternion( [0.1, 0.2, 0.3, -0.4] )
	r = Quaternion( [0.5, 0.6, -0.7, 0.8] )
	print( (q + r - q - r).norm2() )
	print( (q / 1.0 - q).norm2() )
	print( (1.0 / q * q - 1.0).norm2() )
	print( (q * 2.0 - q - q).norm2() )
	print( (q / r * r / q - 1.0).norm2() )
	print( rotation( [1.0, 0.0, 0.0], math.pi / 4.0 ).matrix4() )
	print( rotation( [0.0, 1.0, 0.0], math.pi / 4.0 ).matrix4() )
	print( rotation( [0.0, 0.0, 1.0], math.pi / 4.0 ).matrix4() )
