# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import numpy
import struct
import unicodedata


def argTopoSort( parents ):
	children = [ [] for _ in parents ]
	for i, p in enumerate( parents ):
		if p >= 0:
			children[p].append( i )

	dst = []
	def flatten( i ):
		dst.append( i )
		if len( dst ) > len( parents ):
			raise ValueError()
		for c in children[i]:
			flatten( c )

	for i, p in enumerate( parents ):
		if p < 0:
			flatten( i )

	assert len( dst ) == len( parents )
	return dst


class Material( object ):

	def __init__( self, **kws ):
		for (k, v) in kws.items():
			setattr( self, k, v )


class Loader( object ):

	def load( self, file ):
		self._file = file
		self._loadHeader()
		self._loadInfo()
		self._loadVerts()
		self._loadFaces()
		self._loadTexs()
		self._loadMaterials()
		self._loadBones()

	def _unpack( self, fmt ):
		return struct.unpack( fmt, self._file.read( struct.calcsize( fmt ) ) )

	def _typeSig( self, size ):
		return (
			"B" if size == 1 else
			"H" if size == 2 else
			"i" if size == 4 else
			None
		)

	def _loadHeader( self ):
		magic, ver, size = self._unpack( "4s f B" )
		if magic != b"PMX " or ver < 2.0 or size < 8:
			raise ValueError()

		data = self._unpack( "%dB" % size )
		self._encoding = (
			"utf-16" if data[0] == 0 else
			"utf-8"  if data[0] == 1 else
			None
		)
		self._nUv   = data[1] # # of UVs
		self._tVert = self._typeSig( data[2] ) # type of indices
		self._tTex  = self._typeSig( data[3] ).lower() # type of texture indices
		self._tMat  = self._typeSig( data[4] ).lower() # type of material indices
		self._tBone = self._typeSig( data[5] ).lower() # type of material indices
	
	def _loadStr( self ):
		N  = self._unpack( "i" )
		s, = self._unpack( "%ds" % N )
		return str( s, self._encoding )

	def _loadInfo( self ):
		self._loadStr()
		self._loadStr()
		self._loadStr()
		self._loadStr()
	
	def _loadVerts( self ):
		N, = self._unpack( "i" )
		verts = numpy.recarray( (N,), dtype = [
			("vert", numpy.float32, (3,)),
			("norm", numpy.float32, (3,)),
			("uv",   numpy.float32, (2,)),
		] )
		for i in range( N ):
			verts[i].vert[:] = self._unpack( "3f" )
			verts[i].norm[:] = self._unpack( "3f" )
			verts[i].uv[:]   = self._unpack( "2f" )

			for _ in range( self._nUv ):
				self._unpack( "4f" )

			wt, = self._unpack( "B" )
			if wt == 0:
				self._unpack( self._tBone )
			elif wt == 1:
				self._unpack( "2%s 1f" % self._tBone )
			elif wt == 2:
				self._unpack( "4%s 4f" % self._tBone )
			elif wt == 3:
				self._unpack( "2%s 1f 3f 3f 3f" % self._tBone )
			else:
				ValueError()

			self._unpack( "f" )

		self.verts = verts

	def _loadFaces( self ):
		N, = self._unpack( "i" )
		if N % 3 != 0:
			raise ValueError()

		self.faces = numpy.empty( [N // 3, 3], numpy.uint32 )
		for i in range( N // 3 ):
			self.faces[i, :] = self._unpack( "3%s" % self._tVert )
	
	def _loadTexs( self ):
		N, = self._unpack( "i" )
		self.texs = [ self._loadStr().replace( "\\", "/" ) for _ in range( N ) ]
	
	def _loadMaterials( self ):
		self.materials = []
		N, = self._unpack( "i" )
		bgn = 0
		for _ in range( N ):
			name = unicodedata.normalize( "NFKC", self._loadStr() )
			self._loadStr()
			diffuse = self._unpack( "4f" ) # diffuse
			self._unpack( "3f" ) # specular
			self._unpack( "1f" ) # specular coefficient
			self._unpack( "3f" ) # ambient
			self._unpack( "1B" ) # flag
			self._unpack( "4f" ) # edge color
			self._unpack( "1f" ) # edge size
			tex, = self._unpack( self._tTex ) # normal texure
			self._unpack( self._tTex ) # sphere texure
			self._unpack( "1B" ) # sphere mode
			isToon, = self._unpack( "1B" ) # toon flag
			if isToon == 0:
				self._unpack( self._tTex )
			else:
				self._unpack( "1B" )
			self._loadStr() # memo
			size, = self._unpack( "1i" )
			if size % 3 != 0:
				raise ValueError()

			self.materials.append( Material(
				name    = name,
				diffuse = diffuse,
				tex     = tex,
				bgn     = bgn,
				end     = bgn + size,
			) )
			bgn += size
	
	def _loadBones( self ):
		N, = self._unpack( "i" )
		bones = numpy.recarray( (N,), dtype = [
			("pos",    numpy.float32, (3,)),
			("parent", numpy.int32),
			("after",  numpy.bool),
		] )
		boneMap = {}
		for i in range( N ):
			name = unicodedata.normalize( "NFKC", self._loadStr() )
			boneMap[name] = i
			self._loadStr()
			bones[i].pos[:]  = self._unpack( "3f" )
			bones[i].parent, = self._unpack( self._tBone )
			self._unpack( "1i" )

			flag, = self._unpack( "1H" )
			bones[i].after = flag & 0x1000 != 0
			if flag & 0x0001 == 0:
				self._unpack( "3f" )
			else:
				self._unpack( self._tBone )
			if flag & (0x0100 | 0x0200) != 0:
				self._unpack( self._tBone )
				self._unpack( "1f" )
			if flag & 0x0400 != 0:
				self._unpack( "3f" )
			if flag & 0x0800 != 0:
				self._unpack( "3f" )
				self._unpack( "3f" )
			if flag & 0x2000 != 0:
				self._unpack( "1i" )
			if flag & 0x0020 != 0:
				tb, = self._unpack( self._tBone )
				self._unpack( "1i" )
				self._unpack( "1f" )
				nLink, = self._unpack( "1i" )
				for _ in range( nLink ):
					lb, = self._unpack( self._tBone )
					c, = self._unpack( "1B" )
					if c != 0:
						self._unpack( "3f" )
						self._unpack( "3f" )

		self.bones = bones[argTopoSort( bones.parent )]
		self.boneMap = boneMap
