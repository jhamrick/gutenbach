/*  R e m c t l S e r v e r
 **
 **  The Java client for a service for remote execution of predefined
 **  commands. Access is authenticated via GSS-API Kerberos 5.  It is
 **  up to the server side to perform authorization, perhaps
 **  via aclfiles.
 **
 **  Also contained here is logic to implement a simple Java-based
 **  Remctl server.  The logic here will perform GSS-API Kerberos 5
 **  based server side authorization, save principal names, collect
 **  command arguments, and invoke a single externally provided
 **  "RemctlServer.Servlet".  It is up to that servletjavax.security.auth.callback.CallbackHandler to perform
 **  any authorization checks and implement the functionality of
 **  any commands.
 **
 **  Written by Anton Ushakov <antonu@stanford.edu>
 **  Copyright 2002 Board of Trustees, Leland Stanford Jr. University
 **  See LICENSE for licensing terms.
 **
 **  This version considerably modified by Marcus Watts <mdw@umich.edu>
 **  Updated to use V2 protocol & to support the server side as well.
 **  July 2007
 */

package org.eyrie.eagle.remctl;

import org.ietf.jgss.*;

import java.net.*;
import java.io.*;
import java.util.ArrayList;
import java.nio.ByteBuffer;
import org.eyrie.eagle.remctl.Remctl;

//XXX to do:
//improve documentation
//think about names.
//can byte[] and other string allocation be reduced?
//errors use throw.  server side errors should result
//in MESSAGE_ERROR not unhandled exceptions.
//logging.  how to do it?
//extra debugging.  how to enable?
//additional inline todo items marked XXX


public class RemctlServer extends Remctl {
	// XXX this isn't really a servlet, or is it?
	public interface Servlet {
		public int run(RemctlServer server, String[] args)
		throws GSSException, IOException;
	}

//	XXX passing in serverCreds does bcs case great.  can this
//	also work with jaas?
//	XXX this should be done in a separate thread per request.
//	what form of helper code for this?
	/* make a server */
	public RemctlServer(Socket p_socket,
			GSSCredential serverCreds)
	throws GSSException, IOException 
	{
		GSSManager manager = GSSManager.getInstance();
		socket = p_socket;	/* presumably from ss.accept(); */
		inStream =  new DataInputStream(
				new BufferedInputStream(socket.getInputStream(),8192));
		outStream = new DataOutputStream(
				new BufferedOutputStream(socket.getOutputStream(),8192));
		context = manager.createContext(serverCreds);
		returnCode = 0;
		responseBytes = ByteBuffer.allocate(768);
//		XXX should this just do serve_a_client() here?
	}

	public int make_error(int code, String s)
	throws GSSException, IOException 
	{
		if (returnCode != 2) return -2;
		byte[] bytes = s.getBytes();
		if (bytes.length == 0) return -1;
		ByteBuffer mb = ByteBuffer.allocate(bytes.length + 10);
		mb.put(MESSAGE_V2);
		mb.put(MESSAGE_ERROR);
		mb.putInt(code);
		mb.putInt(bytes.length);
		mb.put(bytes);
//		System.out.println("writing an error");
		write_some_bytes(mb.array());
		returnCode = 3;
		return -1;
	}

	// XXX does not check for TOKEN_MAX_DATA
	// XXX make_output, make_out and make_er should be replaced with
	// Writer streams.  Should have finite buffer.  flush() should
	// cause output to be sent.
	public void make_output(byte where, String s)
	throws GSSException, IOException 
	{
		if (returnCode != 2) return;
		byte[] bytes = s.getBytes();
		if (bytes.length == 0) return;
		ByteBuffer mb = ByteBuffer.allocate(bytes.length + 7);
		mb.put(MESSAGE_V2);
		mb.put(MESSAGE_OUTPUT);
		mb.put(where);
		mb.putInt(bytes.length);
		mb.put(bytes);
//		System.out.println("writing some output");
		write_some_bytes(mb.array());
	}

	public void make_out(String s)
	throws GSSException, IOException 
	{
		make_output((byte)1, s);
	}

	public void make_err(String s)
	throws GSSException, IOException 
	{
		make_output((byte)2, s);
	}

	// XXX big.  can this be broken up?
	public void serve_a_client(Servlet servlet)
	throws GSSException, IOException 
	{
		byte state = TOKEN_V2_INIT;
		client_loop:
			while (keptalive || returnCode != 0) {
				outStream.flush();
//				System.out.println("server input state=" + state);
				byte[] token = read_a_token(state);
				switch(state) {
				default:
					throw new IOException("remctl: I am sick.");
				case TOKEN_V2_INIT:
					if (token.length != 0) {
						throw new IOException("remctl: initstate given data?");
					}
					state = TOKEN_V2_CTX;
					continue;
				case TOKEN_V2_CTX:
					token = context.acceptSecContext(token, 0, token.length);
					if (token != null) {
						outStream.writeByte(state);
						outStream.writeInt(token.length);
						outStream.write(token);
						outStream.flush();
					}
					if (context.isEstablished()) {
						state = TOKEN_V2_RUN;
						clientIdentity = context.getSrcName().toString();
						serverIdentity = context.getTargName().toString();
						// XXX any authorization to do here?
					}
					continue;
				case TOKEN_V2_RUN:
					break;
				}
				byte[] bytes = context.unwrap(token, 0, token.length, prop);
				ByteBuffer messageBuffer = ByteBuffer.allocate(bytes.length);
				messageBuffer.put(bytes);
				messageBuffer.rewind();
				byte cmd = messageBuffer.get();
				if (cmd != MESSAGE_V2) {
					throw new IOException("remctl: Message protocol version was " + cmd + " not 2?");
				}
				cmd = messageBuffer.get();
				switch( cmd ) {
				default:
					throw new IOException("remctl: bad message type " + cmd);
				case MESSAGE_QUIT:
					if (messageBuffer.remaining() != 0) {
						throw new IOException("remctl: MESSAGE_QUIT had junk!");
					}
					break client_loop;
				case MESSAGE_COMMAND:
					break;
				}
				keptalive = messageBuffer.get() != 0;
				byte continue_status = messageBuffer.get();
				/* cs  old rc  new rc
		   0    0       2
		   1    0       1
		   2    1	1
		   3    1       2 */
				if (((continue_status & ~3) != 0)
						|| ((continue_status & 2) >> 1) != returnCode) {
					throw new IOException("remctl: command continuation error");
				}
				returnCode = 2-(((continue_status + 1) & 2)>>1);
				bytes = new byte[messageBuffer.remaining()];
				messageBuffer.get(bytes);
				// XXX grunt.  this can be separate routine "grow" elsewhere.
				if (bytes.length > responseBytes.remaining()) {
					int size = responseBytes.remaining() + bytes.length;
					size = (3 * size)/2;
					ByteBuffer temp = ByteBuffer.allocate(size);
					temp.put(responseBytes.array());
					temp.position(responseBytes.position());
					responseBytes = temp;
				}
				responseBytes.put(bytes);
				if (returnCode != 2) continue;
				responseBytes.flip();
				int argc = responseBytes.getInt();
				ArrayList StringArgs = new ArrayList(argc);
				for (int i = 0; i < argc; ++i) {
					bytes = new byte[responseBytes.getInt()];
					responseBytes.get(bytes);
					StringArgs.add(new String(bytes));
				}
				if (responseBytes.remaining() != 0) {
					throw new IOException("remctl: command has trailing junk");
				}
				responseBytes.rewind();
				responseBytes.limit(responseBytes.capacity());
				String[] args = new String[StringArgs.size()];
				for (int i = 0; i < StringArgs.size(); ++i)
					args[i] = (String) StringArgs.get(i);
				// XXX any authorization to do here?
				int rc = servlet.run(this, args);
				if (returnCode == 2) {
					bytes = new byte[3];
					bytes[0] = MESSAGE_V2;
					bytes[1] = MESSAGE_STATUS;
					bytes[2] = (byte) rc;
//					System.out.println("writing status");
					write_some_bytes(bytes);
				}
				returnCode = 0;
			}
		// XXX these should be done in a "finally"
		context.dispose();
		outStream.flush();
		// XXX should close socket real close to here.
	}
	// XXX can a server main() be used as well?  it should
	//  use a configuration file and the class loader
	//  to map what servelets are available.
}

/*
 **  Local variables:
 **  java-basic-offset: 4
 **  indent-tabs-mode: nil
 **  end:
 */
