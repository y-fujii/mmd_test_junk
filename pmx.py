# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import numpy
import struct


class Material( object ):

	def __init__( self, **kws ):
		for (k, v) in kws.items():
			setattr( self, k, v )


class Loader( object ):

	def load( self, file ):
		self.file = file
		self.loadHeader()
		self.loadInfo()
		self.loadVerts()
		self.loadFaces()
		self.loadTexs()
		self.loadMaterials()

	def unpack( self, fmt ):
		return struct.unpack( fmt, self.file.read( struct.calcsize( fmt ) ) )

	def typeSig( self, size ):
		return (
			"B" if size == 1 else
			"H" if size == 2 else
			"i" if size == 4 else
			None
		)

	def loadHeader( self ):
		magic, ver, size = self.unpack( "4s f B" )
		if magic != b"PMX " or ver < 2.0 or size < 8:
			raise IOError()

		data = self.unpack( "%dB" % size )
		self.encoding = (
			"utf-16" if data[0] == 0 else
			"utf-8"  if data[0] == 1 else
			None
		)
		self.nUv   = data[1] # # of UVs
		self.tVert = self.typeSig( data[2] ) # size of indices
		self.tTex  = self.typeSig( data[3] ).lower() # size of texture indices
		self.tMat  = self.typeSig( data[4] ).lower() # size of material indices
		self.tBone = self.typeSig( data[5] ).lower() # size of material indices
	
	def loadStr( self ):
		N = self.unpack( "i" )
		s, = self.unpack( "%ds" % N )
		return unicode( s, self.encoding )

	def loadInfo( self ):
		self.nameJa = self.loadStr()
		self.nameEn = self.loadStr()
		self.commJa = self.loadStr()
		self.commEn = self.loadStr()
	
	def loadVerts( self ):
		N, = self.unpack( "i" )
		self.verts = numpy.zeros( [N, 3], numpy.float32 )
		self.norms = numpy.zeros( [N, 3], numpy.float32 )
		self.uvs   = numpy.zeros( [N, 2], numpy.float32 )
		for i in range( N ):
			self.verts[i, :] = self.unpack( "3f" )
			self.norms[i, :] = self.unpack( "3f" )
			self.uvs[i, :]   = self.unpack( "2f" )

			for _ in range( self.nUv ):
				self.unpack( "4f" )

			wt, = self.unpack( "B" )
			if wt == 0:
				self.unpack( self.tBone )
			elif wt == 1:
				self.unpack( "2%s 1f" % self.tBone )
			elif wt == 2:
				self.unpack( "4%s 4f" % self.tBone )
			elif wt == 3:
				self.unpack( "2%s 1f 3f 3f 3f" % self.tBone )
			else:
				IOError()

			self.unpack( "f" )

	def loadFaces( self ):
		N, = self.unpack( "i" )
		if N % 3 != 0:
			raise IOError()

		self.faces = numpy.zeros( [N // 3, 3], numpy.uint32 )
		for i in range( N // 3 ):
			self.faces[i, :] = self.unpack( "3%s" % self.tVert )
	
	def loadTexs( self ):
		N, = self.unpack( "i" )
		self.texs = [ self.loadStr().replace( "\\", "/" ) for _ in range( N ) ]
	
	def loadMaterials( self ):
		self.materials = []
		N, = self.unpack( "i" )
		bgn = 0
		for _ in range( N ):
			name = self.loadStr()
			self.loadStr()
			diffuse = self.unpack( "4f" ) # diffuse
			self.unpack( "3f" ) # specular
			self.unpack( "1f" ) # specular coefficient
			self.unpack( "3f" ) # ambient
			self.unpack( "1B" ) # flag
			self.unpack( "4f" ) # edge color
			self.unpack( "1f" ) # edge size
			tex, = self.unpack( self.tTex ) # normal texure
			self.unpack( self.tTex ) # sphere texure
			self.unpack( "1B" ) # sphere mode
			isToon, = self.unpack( "1B" ) # toon flag
			if isToon == 0:
				self.unpack( self.tTex )
			else:
				self.unpack( "1B" )
			self.loadStr() # memo
			size, = self.unpack( "1i" )
			if size % 3 != 0:
				raise IOError()

			self.materials.append( Material(
				name    = name,
				diffuse = diffuse,
				tex     = tex,
				bgn     = bgn,
				end     = bgn + size,
			) )
			bgn += size
