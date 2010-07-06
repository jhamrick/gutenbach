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

import javax.security.auth.login.*;
import javax.security.auth.Subject;
//GNU*/import gnu.javax.security.auth.callback.ConsoleCallbackHandler;
/*SUN*/import com.sun.security.auth.callback.TextCallbackHandler;
import org.ietf.jgss.*;

import java.net.*;
import java.io.*;
import java.util.ArrayList;
import java.util.Iterator;
import java.nio.ByteBuffer;
import java.security.PrivilegedExceptionAction;

//XXX to do:
//improve documentation
//think about names.
//can byte[] and other string allocation be reduced?
//errors use throw.  server side errors should result
//in MESSAGE_ERROR not unhandled exceptions.
//logging.  how to do it?
//extra debugging.  how to enable?
//additional inline todo items marked XXX


public class RemctlClient extends Remctl {
	private String servicePrincipal;

	private Writer out, err;

	/**
	 * Factory method that creates a <code>LogincContext</code>
	 * and returns a RemctlClient that executed from within that
	 * context.
	 *
	 * @param args  array of args to pass to remctl server
	 * @param host  host name of remctl server. 
	 * @param port  port of remctl server. If 0, uses the default
	 *              port of 4373 (Remctl.DEFAULT_PORT).
	 * @param princ Principal to use. If null, uses the default
	 *              principal of <code>"host/"+host</code>.
	 * @param lcName  Name passed to the <code>LoginContext</code> constructor.
	 *              If null, use the default name of "Remctl".
	 */

//	XXX this uses jaas.  can bcs be done as well somehow?
	public static RemctlClient withLogin(final String args[],
			final String host,
			final int port,
			final String princ,
			final String lcName)
	throws javax.security.auth.login.LoginException,
	java.security.PrivilegedActionException
	{
		final LoginContext lc = 
			new LoginContext(lcName != null ? lcName : DEFAULT_NAME, 
//GNU*/					new ConsoleCallbackHandler());
/*SUN*/					new TextCallbackHandler());
		lc.login();
		PrivilegedExceptionAction pea = 
			new PrivilegedExceptionAction() {
			public Object run() 
			throws GSSException,
			IOException
			{
				return new RemctlClient(args, 
						host,
						port,
						princ,
						System.out,
						System.err);
			}
		};

		try {
			return (RemctlClient)
			Subject.doAsPrivileged(lc.getSubject(), pea, null);
		} finally {
			lc.logout();
		}
	}

	/**
	 * Factory method that creates a <code>LogincContext</code>
	 * and returns a RemctlClient that executed from within that
	 * context. Uses default values for port/principal/name.
	 *
	 * @param args  array of args to pass to remctl server
	 * @param host  host name of remctl server. 
	 *              If null, use the default name of "RemctlClient".
	 */
	public static RemctlClient withLogin(final String args[],
			final String host)
	throws javax.security.auth.login.LoginException,
	java.security.PrivilegedActionException
	{ 
		return withLogin(args, host, 0, null, null);
	}

	/**
	 * Invoke Remctl on the specified host, with the specified args.
	 * If no exceptions are thrown, you would then normally check
	 * the return code with <code>getReturnCode()</code>, and the
	 * returned message with <code>getReturnMessage()</code>.
	 * <p>
	 * Should only be called within a login context that has the
	 * proper Kerberos credentials. The factory methods <code>withLogin</code>
	 * can be used when a single RemctlCLient object is needed. If
	 * multiple RemctlClient objects are needed, then the application
	 * should itself set up the login context, invoke Subject.doAsPrivileged,
	 * and then create multiple RemctlObjects from within that context.
	 *
	 * @param args  array of args to pass to remctl server
	 * @param host  host name of remctl server. 
	 * @param port  port of remctl server. If 0, uses the default
	 *              port of 4373 (Remctl.DEFAULT_PORT).
	 * @param servicePrincipal Principal to use. If null, uses the default
	 *              principal of <code>"host/"+host</code>.
	 * @param p_out Writer to receive stdout from remote job.
	 * @param p_err Writer to receive stderr from remote job.
	 */
	public RemctlClient(String args[], 
			String host, 
			int port, 
			String servicePrincipal,
			Writer p_out,
			Writer p_err)
	throws GSSException, IOException 
	{
		this(host,port,servicePrincipal,p_out,p_err);
		this.clientEstablishContext();
		this.process(false, args);
		this.finishup();
	}
	public RemctlClient(String args[], 
			String host, 
			int port, 
			String servicePrincipal,
			PrintStream p_out,
			PrintStream p_err)
	throws GSSException, IOException 
	{
		this(args,host,port,servicePrincipal,
				new PrintWriter(p_out, true), new PrintWriter(p_err, true));
	}

	public RemctlClient(String args[], 
			String host, 
			int port, 
			String servicePrincipal)
	throws GSSException, IOException 
	{
		this(args,host,port,servicePrincipal,System.out, System.err);
	}

	public RemctlClient(String host, 
			int port, 
			String servicePrincipal,
			Writer p_out,
			Writer p_err)
	throws GSSException, IOException 
	{
		this.servicePrincipal = servicePrincipal;

		out = p_out;
		err = p_err;

		InetAddress hostAddress = InetAddress.getByName(host);
		String hostName = hostAddress.getCanonicalHostName().toLowerCase();
		if (this.servicePrincipal == null) 
			this.servicePrincipal = "host/"+hostName;

		/* Make the socket: */
		socket =    new Socket(hostName, port != 0 ? port : DEFAULT_PORT);
		inStream =  new DataInputStream(
				new BufferedInputStream(socket.getInputStream(),8192));
		outStream = new DataOutputStream(
				new BufferedOutputStream(socket.getOutputStream(),8192));
	}

	public RemctlClient(String host, 
			int port, 
			String servicePrincipal,
			Writer p_out,
			Writer p_err,
			final LoginContext lc)
	throws GSSException, IOException 
	{
		this(host,port,servicePrincipal,p_out,p_err);
		PrivilegedExceptionAction pea = 
			new PrivilegedExceptionAction() {
			public Object run()
			throws GSSException, IOException {
				clientEstablishContext();
				return RemctlClient.this;
			}
		};
		try {
			Subject.doAsPrivileged(lc.getSubject(), pea, null);
		} catch (Exception e) {	// no causes in 1.5.0
			throw new IOException("remctl: failed to establish context");
		}
	}

	public void process(boolean keepalive, String args[])
	throws GSSException, IOException 
	{
		if (!keptalive) {
			returnCode = -1;
			return;
		}
		ArrayList byteArgs;

		byteArgs = new ArrayList();
		for (int i=0; i < args.length; i++) {
			byteArgs.add(args[i].getBytes());
		}
		processRequest(byteArgs, keepalive);
		for (;;) {
			switch(processResponse()) {
			case MESSAGE_OUTPUT:
				byte stream = responseBytes.get();
				Writer x;
				x = stream == 1 ? out : err;
				int len = responseBytes.getInt();
				if (len != responseBytes.remaining())
					throw new IOException("remctl: bad MESSAGE_OUTPUT length");
				byte[] m = new byte[len];
				responseBytes.get(m);
				x.write(new String(m));
				x.flush();
				continue;
			case MESSAGE_STATUS:
				byte status = responseBytes.get();
				if (0 != responseBytes.remaining())
					throw new IOException("remctl: bad MESSAGE_STATUS length");
				// XXX how to indicate cmd ended by status?
				returnCode = status;
				break;
			case MESSAGE_ERROR:
				status = (byte) responseBytes.getInt();
				len = responseBytes.getInt();
				if (len != responseBytes.remaining())
					throw new IOException("remctl: bad MESSAGE_ERROR length");
				err.write(new String(responseBytes.array()) + "\n");
				err.flush();
				// XXX how to indicate cmd ended by error?
				returnCode = status;
				break;
			case MESSAGE_VERSION:
				stream = responseBytes.get();
				if (stream >= MESSAGE_V2)
					continue;
				processQuit();
				returnCode = -1;
				// XXX how to indicate cmd ended due to protocol?
				break;
			default:
				// XXX how to indicate cmd ended by protocol?
				throw new IOException("remctl: bad message type");
			}
			break;
		}
	}

	public void process(String args[])
	throws GSSException, IOException 
	{
		this.process(true, args);
	}

	public void finishup()
	throws GSSException, IOException 
	{
		processQuit();
		context.dispose();
		out.flush();
		err.flush();
		outStream.flush();
		socket.close();
	}

	public void clientEstablishContext() 
	throws GSSException, IOException {

		if (!keptalive) return;
		/*
		 * This Oid is used to represent the Kerberos version 5 GSS-API
		 * mechanism. It is defined in RFC 1964. We will use this Oid
		 * whenever we need to indicate to the GSS-API that it must
		 * use Kerberos for some purpose.
		 */
		Oid krb5Oid = new Oid("1.2.840.113554.1.2.2");

		GSSManager manager = GSSManager.getInstance();

		/*
		 * Create a GSSName out of the service name. The null
		 * indicates that this application does not wish to make
		 * any claims about the syntax of this name and that the
		 * underlying mechanism should try to parse it as per whatever
		 * default syntax it chooses.
		 */
		GSSName serverName = manager.createName(servicePrincipal, null);

		/*
		 * Create a GSSContext for mutual authentication with the
		 * server.
		 *    - serverName is the GSSName that represents the server.
		 *    - krb5Oid is the Oid that represents the mechanism to
		 *      use. The client chooses the mechanism to use.
		 *    - null is passed in for client credentials
		 *    - DEFAULT_LIFETIME lets the mechanism decide how long the
		 *      context can remain valid.
		 * Note: Passing in null for the credentials asks GSS-API to
		 * use the default credentials. This means that the mechanism
		 * will look among the credentials stored in the current Subject
		 * to find the right kind of credentials that it needs.
		 */
		context = manager.createContext(serverName,
				krb5Oid,
				null,
				GSSContext.DEFAULT_LIFETIME);

		// Set the optional features on the context.
		context.requestMutualAuth(true);  // Mutual authentication
		context.requestConf(true);  // Will use confidentiality later
		context.requestInteg(true); // Will use integrity later


		byte[] token = new byte[0];

		// Initialize the context establishment 
		outStream.writeByte(TOKEN_V2_INIT);
		outStream.writeInt(token.length);
		outStream.write(token);
		outStream.flush();

		// Do the context establishment loop
		while (!context.isEstablished()) {

			// token is ignored on the first call
			token = context.initSecContext(token, 0, token.length);

			// Send a token to the server if one was generated by
			// initSecContext
			if (token != null) {
				outStream.writeByte(TOKEN_V2_CTX);
				outStream.writeInt(token.length);
				outStream.write(token);
				outStream.flush();
			}

			// If the client is done with context establishment
			// then there will be no more tokens to read in this loop
			if (!context.isEstablished()) {
				// flag
//				System.out.println("continuing client authentication");
				token = read_a_token(TOKEN_V2_CTX);
			}
		}

		clientIdentity = context.getSrcName().toString();
		serverIdentity = context.getTargName().toString();

		/*
		 * If mutual authentication did not take place, then only the
		 * client was authenticated to the server. Otherwise, both
		 * client and server were authenticated to each other.
		 */
		if (! context.getMutualAuthState()) {
			throw new IOException("remctl: no mutal authentication");
		}

	}

	private void processRequest(ArrayList byteArgs, boolean keepalive)
	throws GSSException, IOException {
		/* determine size of buffer we need */
		int messageLength = 8; /* v2+cmd+kp+cs+ac0+ac1+ac2+ac3 */
		byte continue_status = 1;
		for (Iterator it = byteArgs.iterator(); it.hasNext();) {
			/* add 4 for the length, then the actual length */
			byte[]  bytes = (byte[]) it.next();
			messageLength += 4+bytes.length;	/* szn + argn */
		}
		ByteBuffer messageBuffer = ByteBuffer.allocate(messageLength);

		/* Make the message buffer */
		messageBuffer.put(MESSAGE_V2);
		messageBuffer.put(MESSAGE_COMMAND);
		messageBuffer.put((byte)(keepalive ? 1 : 0));
		messageBuffer.put(continue_status);	/* will ignore */
		messageBuffer.putInt(byteArgs.size());
		for (Iterator it = byteArgs.iterator(); it.hasNext(); ) {
			byte[]  bytes = (byte[]) it.next();
			messageBuffer.putInt(bytes.length);
			messageBuffer.put(bytes);
		}

		messageBuffer.put(3, continue_status);
		messageBuffer.flip();

		while (messageBuffer.hasRemaining()) {
			int count = (messageBuffer.remaining());
			int pos;
			if (messageBuffer.position() != 0) count += 4;
			if (count > TOKEN_MAX_DATA) count = TOKEN_MAX_DATA;
			byte[] messageBytes = new byte[count];
			if ((pos = messageBuffer.position()) != 0) {
				messageBuffer.position(0);
				messageBuffer.get(messageBytes, 0, 3);
				messageBuffer.position(pos);
				messageBuffer.get(messageBytes, 4, count-4);
			} else {
				messageBuffer.get(messageBytes, 0, count);
			}
			if (!messageBuffer.hasRemaining())
				continue_status ^= 1;	/* 1 => 0, 2 => 3 */
			messageBytes[3] = continue_status;
//			System.out.println("writing a command cs=" + continue_status);
			continue_status = 2;
			write_some_bytes(messageBytes);
		}
		outStream.flush();
		keptalive = keepalive;
	}

	private void processQuit() throws GSSException, IOException {
		if (!keptalive) return;
		keptalive = false;
		byte[] messageBytes = new byte[2];
		messageBytes[0] = MESSAGE_V2;
		messageBytes[1] = MESSAGE_QUIT;
//		System.out.println("writing quit");
		write_some_bytes(messageBytes);
		outStream.flush();
	}

	private byte processResponse() throws GSSException, IOException {

		byte returnType;

//		System.out.println("client reading response");
		byte[] token = read_a_token(TOKEN_V2_RUN);

		byte[] bytes = context.unwrap(token, 0, token.length, prop);
		ByteBuffer messageBuffer = ByteBuffer.allocate(bytes.length);
		messageBuffer.put(bytes);
		messageBuffer.rewind();
		returnType = messageBuffer.get();
		if (returnType != MESSAGE_V2)
			throw new IOException("remctl: Message protocol version was " + returnType + " not 2?");
		returnType = messageBuffer.get();
		responseBytes = messageBuffer.slice();
		return returnType;
	}

	/**
	 * Main should be invoked as follows:
	 * <p>
	 * <code>java -Djava.security.auth.login.config=login.conf RemctlTool {host} {args}</code>
	 *
	 */

	// XXX should note this is a convenience test interface
	//  not "the way" to call this.
	public static void main(String[] args) {

		if (args.length < 3) {
			System.err.println("Usage: java <options> RemctlTool "
					+ " <hostName> <args>");
			System.exit(-1);
		}

		try {

			String host = args[0];
			String remargs[] = new String[args.length-1];
			for(int i=1; i<args.length; i++)
				remargs[i-1] = args[i];

			RemctlClient rc = RemctlClient.withLogin(remargs,
					host,
					0,
					null,
					null);
			System.exit(rc.getReturnCode());
		} catch (Exception e) {
			System.err.println("Error: "+e.getMessage());
			e.printStackTrace();
			System.exit(-1);
		}

	}
}

/*
 **  Local variables:
 **  java-basic-offset: 4
 **  indent-tabs-mode: nil
 **  end:
 */
