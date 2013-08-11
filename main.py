#!/usr/bin/python3
# encoding: utf-8
# by Yasuhiro Fujii <y-fujii at mimosa-pudica.net>, public domain

from pprint import pprint
import math
import bisect
import time
import io
import numpy
from OpenGL.GL import *
from PIL import Image
import matrix3d
import quaternion
import glutils
import pmx
import vmd


class Renderer( object ):

	vertSrc = """
		#version 120
		uniform int uType;
		uniform mat4 uM;
		attribute vec3 aP;
		attribute vec3 aN;
		attribute vec2 aUv;
		varying vec2 vUv;
		varying vec3 vI;

		const float a = 0.85;
		const vec3 Lh = normalize( vec3( +0.0, +1.0, +0.0 ) );
		const vec3 Ll = normalize( vec3( -1.0, +1.0, -1.0 ) );
		const vec3 colTop = vec3( 0.00, 0.25, 0.50 ) * a + vec3( 0.5, 0.5, 0.5 ) * (1.0 - a);
		const vec3 colBot = vec3( 0.25, 0.25, 0.25 ) * a + vec3( 0.5, 0.5, 0.5 ) * (1.0 - a);
		const vec3 colPar = vec3( 0.50, 0.25, 0.00 ) * a + vec3( 0.0, 0.0, 0.0 ) * (1.0 - a);

		void main() {
			gl_Position = uM * vec4( aP, 1.0 );
			vec3 N = normalize( mat3( uM ) * aN );
			vUv = aUv;

			vec3 I = (
				(colTop + colBot) +
				dot( N, Lh ) * (colTop - colBot) +
				max( dot( N, Ll ), 0.0 ) * colPar
			);
			if( uType == 0 ) {
				vI = I;
			}
			else if( uType == 1 ) {
				vI = vec3( 0.70, I[1], I[2] );
			}
			else if( uType == 2 ) {
				vI = vec3( 0.70, 0.70, 0.70 );
			}
			else {
				vI = vec3( 0.00, 0.00, 0.00 );
			}
		}
	"""

	fragSrc = """
		#version 120
		uniform sampler2D uTex;
		varying vec2 vUv;
		varying vec3 vI;

		void main() {
			gl_FragColor = texture2D( uTex, vUv ) * vec4( sqrt( vI ), 1.0 );
		}
	"""

	def __init__( self, model, motion ):
		self.model  = model
		self.motion = motion
		self.bones = numpy.recarray( (model.bones.shape[0],), dtype = [
			("rLoc", numpy.float32, (3,)),
			("rRot", numpy.float32, (4,)),
			("aLoc", numpy.float32, (3,)),
			("aRot", numpy.float32, (4,)),
			("aMat", numpy.float32, (4, 4)),
		] )
		self.frame = 0

		for (i, tex) in enumerate( model.texs ):
			glActiveTexture( GL_TEXTURE0 + i )
			glBindTexture( GL_TEXTURE_2D, i )
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP )
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP )
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR )
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR )
			glutils.loadTexture( numpy.asarray( Image.open( tex ) ) )

		self.shader = glutils.Shader( self.vertSrc, self.fragSrc )
		self.shader.use()
		self.shader.attrib( b"aP",  model.verts.vert )
		self.shader.attrib( b"aN",  model.verts.norm )
		self.shader.attrib( b"aUv", model.verts.uv   )

		glDepthFunc( GL_LEQUAL )
		glEnable( GL_DEPTH_TEST )

		glFrontFace( GL_CW )
		#glCullFace( GL_BACK )
		glEnable( GL_CULL_FACE )

		glBlendFuncSeparate(
			GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
			GL_ONE,       GL_ONE_MINUS_SRC_ALPHA,
		)
		glEnable( GL_BLEND )

	def render( self ):
		arg = (time.time() * (2.0 / math.pi)) % (2.0 * math.pi)

		# XXX: sort transparent polygon
		glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
		self.shader.uniform( b"uM",
			numpy.matrix( [
				[1.0, 0.0, 0.0, 0.0],
				[0.0, 1.0, 0.0, 0.0],
				[0.0, 0.0, 1.0, 0.0],
				[0.0, 0.0, 0.2, 1.0],
			] ) *
			matrix3d.rotate( 0, math.pi / -24.0 ) *
			matrix3d.rotate( 1, arg ) *
			matrix3d.translate( [0.0, -0.9, 0.0] ) *
			matrix3d.scale( 0.09 )
		)

		for m in self.model.materials:
			if m.name.find( "体" ) >= 0 or m.name.find( "skin" ) >= 0:
				self.shader.uniform( b"uType", 1 )
			elif m.name.find( "顔" ) >= 0 or m.name.find( "face" ) >= 0:
				self.shader.uniform( b"uType", 2 )
			elif m.name.find( "目" ) >= 0 or m.name.find( "eye" ) >= 0:
				self.shader.uniform( b"uType", 2 )
			else:
				self.shader.uniform( b"uType", 0 )
			self.shader.uniform( b"uTex", m.tex )

			glDrawElementsui( GL_TRIANGLES, self.model.faces[m.bgn // 3 : m.end // 3] )
	
	def updateFrame( self, frame ):
		bgn = bisect.bisect_left ( self.motion.bones.frame, self.frame )
		end = bisect.bisect_right( self.motion.bones.frame, frame )
		for i in range( bgn, end ):
			boneKey = self.motion.bones[i]
			self.bones[boneKey.bone].rRot = boneKey.rot
			self.bones[boneKey.bone].rLoc = boneKey.loc
		
		timeBgn = time.time()
		#for i in range( len( self.bones ) ):
		#	parent = self.model.bones[i].parent
		#	if parent < 0:
		#		self.bones[i].aRot = self.bones[i].rRot
		#		self.bones[i].aLoc = self.bones[i].rLoc
		#	else:
		#		self.bones[i].aRot = quaternion.mul(
		#			self.bones[i].rRot,
		#			self.bones[parent].aRot
		#		)
		#		self.bones[i].aLoc = quaternion.transform(
		#			self.bones[i].aRot,
		#			self.bones[i].rLoc,
		#		) + self.bones[parent].aLoc
		parents = self.model.bones.parent
		aRots = self.bones.aRot
		aLocs = self.bones.aLoc
		rRots = self.bones.rRot
		rLocs = self.bones.rLoc
		for i in range( len( self.bones ) ):
			parent = parents[i]
			if parent < 0:
				aRots[i] = rRots[i]
				aLocs[i] = rLocs[i]
			else:
				aRots[i] = quaternion.mul( rRots[i], aRots[parent] )
				aLocs[i] = quaternion.transform( aRots[i], rLocs[i] ) + aLocs[parent]
		timeEnd = time.time()

		# too slow...
		print( timeEnd - timeBgn )

		self.frame = frame


from OpenGL import GLUT

class GlutWindow( object ):

	def __init__( self, model, motion ):
		GLUT.glutCreateWindow( "test" )
		GLUT.glutDisplayFunc( self.onDisplay )
		GLUT.glutReshapeFunc( self.onReshape )
		GLUT.glutIdleFunc( self.onIdle )
		self.renderer = Renderer( model, motion )

	def onDisplay( self ):
		self.renderer.render()
		GLUT.glutSwapBuffers()

	def onReshape( self, w, h ):
		l = min( w, h )
		glViewport( (w - l) // 2, (h - l) // 2, l, l )

	def onIdle( self ):
		GLUT.glutPostRedisplay()


from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtOpenGL

class QtWindow( QtOpenGL.QGLWidget ):

	def __init__( self, model, motion ):
		QtOpenGL.QGLWidget.__init__( self )
		self.setWindowFlags( QtCore.Qt.FramelessWindowHint )
		self.setAttribute( QtCore.Qt.WA_TranslucentBackground )
		self.setAttribute( QtCore.Qt.WA_TransparentForMouseEvents )
		self.setWindowOpacity( 0.75 )

		self.model  = model
		self.motion = motion
		self.frame = 0
		self.timeBgn = time.time()
		self.timeFps = 24.0
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect( self.onTimer )
		self.timer.start( 0 )

	def paintGL( self ):
		self.renderer.render()

	def resizeGL( self, w, h ):
		l = min( w, h )
		glViewport( (w - l) // 2, (h - l) // 2, l, l )
	
	def initializeGL( self ):
		self.renderer = Renderer( self.model, self.motion )
	
	def onTimer( self ):
		self.renderer.updateFrame( int( (time.time() - self.timeBgn) * self.timeFps ) )
		self.updateGL()


def main():
	pmxLoader = pmx.Loader()
	with io.open( "test.pmx", "rb" ) as f:
		pmxLoader.load( f )
	print( dir( pmxLoader ) )

	vmdLoader = vmd.Loader()
	with io.open( "test.vmd", "rb" ) as f:
		vmdLoader.load( f, pmxLoader.boneMap, {} )
	print( dir( vmdLoader ) )

	if False:
		GLUT.glutInit()
		GLUT.glutInitDisplayMode( GLUT.GLUT_DOUBLE | GLUT.GLUT_DEPTH | GLUT.GLUT_RGBA )
		window = GlutWindow( pmxLoader, vmdLoader )
		GLUT.glutMainLoop()
	elif True:
		app = QtGui.QApplication( [] )
		widget = QtWindow( pmxLoader, vmdLoader )
		widget.show()
		app.exec_()


main()
