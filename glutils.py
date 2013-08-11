# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

import numpy
from OpenGL.GL import *
from OpenGL.GL import shaders


class Shader( object ):

	def __init__( self, vertSrc, fragSrc ):
		#self.prog = shaders.compileProgram(
		#	shaders.compileShader( vertSrc, GL_VERTEX_SHADER ),
		#	shaders.compileShader( fragSrc, GL_FRAGMENT_SHADER ),
		#)
		vertShader = glCreateShader( GL_VERTEX_SHADER )
		glShaderSource( vertShader, vertSrc )
		glCompileShader( vertShader )
		fragShader = glCreateShader( GL_FRAGMENT_SHADER )
		glShaderSource( fragShader, fragSrc )
		glCompileShader( fragShader )
		self.prog = shaders.compileProgram( vertShader, fragShader )
	
	def use( self ):
		glUseProgram( self.prog )

	def uniform( self, key, val ):
		loc = glGetUniformLocation( self.prog, key )
		if isinstance( val, int ):
			glUniform1i( loc, val )
		elif isinstance( val, float ):
			glUniform1f( loc, val )
		elif isinstance( val, numpy.ndarray ):
			if len( val.shape ) == 1:
				if val.dtype == numpy.int32:
					t = "i"
				elif val.dtype == numpy.float32:
					t = "f"
				else:
					assert False
				getattr( OpenGL.GL, "glUniform%d%sv" % (val.shape[0], t) )( loc, 1, val )
			elif len( val.shape ) == 2:
				assert val.shape[0] == val.shape[1]
				func = getattr( OpenGL.GL, "glUniformMatrix%dfv" % val.shape[0] )
				func( loc, 1, True, val.astype( numpy.float32 ) )
			else:
				assert False
		else:
			assert False

	def attrib( self, key, val ):
		assert len( val.shape ) == 2
		assert val.dtype == numpy.float32
		loc = glGetAttribLocation( self.prog, key )
		glVertexAttribPointer( loc, val.shape[1], GL_FLOAT, False, val.shape[1] * 4, val )
		glEnableVertexAttribArray( loc )


def loadTexture( img ):
	assert len( img.shape ) == 3
	if img.shape[2] == 3:
		fmt = GL_RGB
	elif img.shape[2] == 4:
		fmt = GL_RGBA
	glTexImage2D( GL_TEXTURE_2D, 0, fmt, img.shape[1], img.shape[0], 0, fmt, GL_UNSIGNED_BYTE, img )
