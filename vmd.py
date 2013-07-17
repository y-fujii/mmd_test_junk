# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import struct


class Loader( object ):

	def load( self, file ):
		self.file = file
		magic = self.loadStr( 30 )
		if not magic.startswith( "Vocaloid Motion Data" ):
			raise IOError()
		self.loadStr( 20 )

		self.loadBone()
		self.loadFace()

	def unpack( self, fmt ):
		return struct.unpack( fmt, self.file.read( struct.calcsize( fmt ) ) )

	def loadStr( self, size ):
		s = self.read( size )
		i = s.index( "\0" )
		return unicode( s[:i], "cp932" )

	def loadBone( self ):
		bones = []
		size, = self.unpack( "I" )
		for _ in range( size ):
			name  = self.loadStr( 15 )
			time, = self.unpack( "1I" )
			loc   = self.unpack( "3f" )
			rot   = self.unpack( "4f" )
			self.loadStr( 64 )
			bones.append( (time, name, loc, rot) )
		
		self.bones = sorted( bones )

	def loadFace( self ):
		faces = []
		size, = self.unpack( "I" )
		for _ in range( size ):
			name = self.loadStr( 15 )
			time, value = self.unpack( "I f" )
			faces.append( (time, name, value) )

		self.faces = sorted( faces )
