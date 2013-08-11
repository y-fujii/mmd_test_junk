# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import struct
import numpy
import unicodedata


class Loader( object ):

	def load( self, file, boneMap, skeyMap ):
		self._file = file
		self.boneMap = boneMap
		self.skeyMap = skeyMap
		magic = self._loadStr( 30 )
		if not magic.startswith( "Vocaloid Motion Data" ):
			raise ValueError()
		self._loadStr( 20 )

		self._loadBones()
		self._loadSKeys()

	def _unpack( self, fmt ):
		return struct.unpack( fmt, self._file.read( struct.calcsize( fmt ) ) )

	def _loadStr( self, N ):
		s = self._file.read( N )
		i = s.index( b"\0" )
		return str( s[:i], "cp932" )

	def _loadBones( self ):
		N, = self._unpack( "I" )
		bones = numpy.recarray( (N,), dtype = [
			("frame", numpy.int32),
			("bone",  numpy.int32),
			("loc",   numpy.float32, (3,)),
			("rot",   numpy.float32, (4,)),
		] )
		for i in range( N ):
			name = unicodedata.normalize( "NFKC", self._loadStr( 15 ) )
			bones[i].bone   = self.boneMap.get( name, -1 )
			bones[i].frame  = self._unpack( "1i" )
			bones[i].loc[:] = self._unpack( "3f" )
			bones[i].rot[:] = self._unpack( "4f" )
			self._loadStr( 64 )
		
		self.bones = bones[numpy.argsort( bones.frame )]

	def _loadSKeys( self ):
		N, = self._unpack( "I" )
		skeys = numpy.recarray( (N,), dtype = [
			("frame", numpy.int32),
			("skey",  numpy.int32),
			("val",   numpy.float32),
		] )
		for i in range( N ):
			name = unicodedata.normalize( "NFKC", self._loadStr( 15 ) )
			skeys[i].skey   = self.skeyMap.get( name, -1 )
			skeys[i].frame, = self._unpack( "i" )
			skeys[i].val,   = self._unpack( "f" )

		self.skeys = skeys[numpy.argsort( skeys.frame )]
