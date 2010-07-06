/*  R e m c t l C l i e n t
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
import java.nio.ByteBuffer;

//XXX to do:
//improve documentation
//think about names.
//can byte[] and other string allocation be reduced?
//errors use throw.  server side errors should result
//in MESSAGE_ERROR not unhandled exceptions.
//logging.  how to do it?
//extra debugging.  how to enable?
//additional inline todo items marked XXX

public class Remctl {
	/** Default remctl server port to use */
	public static final int DEFAULT_PORT = 4373;

	/** Default name to use in the login configuration file */
	public static final String DEFAULT_NAME = "RemctlClient";

	protected static final int TOKEN_MAX_DATA =         65536;

	/* Token types */
	protected static final byte TOKEN_NOOP  =           1;
	protected static final byte TOKEN_CONTEXT =         2;
	protected static final byte TOKEN_DATA =            4;
	protected static final byte TOKEN_MIC =             8;

	/* Token flags */
	protected static final byte TOKEN_CONTEXT_NEXT =    16;
	protected static final byte TOKEN_SEND_MIC =        32;
	protected static final byte TOKEN_PROTOCOL =        64;

	/* V2 only uses these flag combinations */
	protected static final byte TOKEN_V2_INIT =         TOKEN_NOOP|TOKEN_CONTEXT_NEXT|TOKEN_PROTOCOL;
	protected static final byte TOKEN_V2_CTX =          TOKEN_CONTEXT|TOKEN_PROTOCOL;
	protected static final byte TOKEN_V2_RUN =          TOKEN_DATA|TOKEN_PROTOCOL;

	/* Message types */
	protected static final byte MESSAGE_COMMAND =       1;
	protected static final byte MESSAGE_QUIT =          2;
	protected static final byte MESSAGE_OUTPUT =        3;
	protected static final byte MESSAGE_STATUS =        4;
	protected static final byte MESSAGE_ERROR =         5;
	protected static final byte MESSAGE_VERSION =       6;

	protected static final byte MESSAGE_V2 =            2;

	public static final int ERROR_INTERNAL =         1;
	public static final int ERROR_BAD_TOKEN =        2;
	public static final int ERROR_UNKNOWN_MESSAGE =  3;
	public static final int ERROR_BAD_COMMAND =      4;
	public static final int ERROR_UNKNOWN_COMMAND =  5;
	public static final int ERROR_ACCESS =           6;
	public static final int ERROR_TOOMANY_ARGS =     7;
	public static final int ERROR_TOOMUCH_DATA =     8;

	protected ByteBuffer responseBytes;
	protected GSSContext context;
	/*
	 * The first MessageProp argument is 0 to request
	 * the default Quality-of-Protection.
	 * The second argument is true to request
	 * privacy (encryption of the message).
	 */
	protected static MessageProp prop = new MessageProp(0, true);
	public Socket socket;
	protected DataInputStream inStream;
	protected DataOutputStream outStream;
	protected boolean keptalive = true;
	protected String clientIdentity;
	protected String serverIdentity;
	protected int returnCode;

	/**
	 * Returns the client's Kerberos principal name.
	 *
	 * @return Returns the client's Kerberos principal name.
	 *
	 */
	public String getClientIdentity() {
		return clientIdentity;
	}

	/**
	 * Returns the server's Kerberos principal name.
	 *
	 * @return Returns the server's Kerberos principal name.
	 *
	 */
	public String getServerIdentity() {
		return serverIdentity;
	}

	public int getReturnCode() {
		return returnCode;
	}

	protected void write_some_bytes(byte[] bytes)
	throws GSSException, IOException 
	{
		byte[] token = context.wrap(bytes, 0, bytes.length, prop);
		outStream.writeByte(TOKEN_V2_RUN);
		outStream.writeInt(token.length);
		outStream.write(token);
	}

	protected byte[] read_a_token(byte state)
	throws GSSException, IOException 
	{
		byte flag = inStream.readByte();
		// XXX is throwing an exception best?
		if (flag != state) {
			throw new IOException("remctl: Wrong token type received, got " +
					flag + " expected " + state);
		}
		byte[] token = new byte[inStream.readInt()];
		inStream.readFully(token);
		return token;
	}
}

/*
 **  Local variables:
 **  java-basic-offset: 4
 **  indent-tabs-mode: nil
 **  end:
 */
