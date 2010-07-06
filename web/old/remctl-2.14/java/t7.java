/*  t 7
**
**  This implements a trivial remctl server instance,
**  useful for test purposes, and also serves as a
**  demonstration of how to use the server logic in
**  RemctlServer.  The "name : value" style output is
**  conveniently compatible with the expectations of t5.java .
**
**  Written by Marcus Watts <mdw@umich.edu>
**  July 2007
*/

import org.ietf.jgss.*;

import java.net.*;
import java.io.*;
import java.util.Date;
import java.util.Calendar;
import java.text.SimpleDateFormat;

import org.eyrie.eagle.remctl.*;

public class t7 {
    /**
     * Main should be invoked as follows:
     * <p>
     * <code>java -Djavax.security.auth.useSubjectCredsOnly=false \
     * -Djava.security.auth.login.config=bcsKeytab.conf t7 princ port</code>
     *
     */

	/* java times are # of milliseconds since 1970.
	 *  Let's output that as seconds; in c: %d.%03d
	 */
    private static String mytime(Date t) {
	Long x = t.getTime();
	Long ms = x % 1000L;
	Long s = x / 1000L;
	ms += 1000;
	String s_ms1000 = ms.toString();
	return s + "." + s_ms1000.substring(1);
    }

	/* this is simulates a simple application.
	 * it prints stuff on output, emits an error
	 * message, and return an exit code.
	 * args[0] is the cmd name - for the special case
	 *  "error" this errors out.
	 * if args[0] is "rc" - this does a exit(atoi(argv[1]);
	 *
	 * In a real application, getClientIdentity would probably
	 * be used for some form of authorization.
	 */

    static class t7_servlet implements RemctlServer.Servlet {
	public int run (RemctlServer server, String[] args)
	throws IOException, GSSException {
System.out.println(" t7_servelet runs");
	    if (args[0].compareTo("error") == 0)
		return server.make_error(Remctl.ERROR_BAD_COMMAND, "Bad command");
	    StringWriter my_out = new StringWriter();
	    StringWriter my_err = new StringWriter();
	    my_out.write("Command:");
	    for (int i = 0; i < args.length; ++i) {
		my_out.write(" " + args[i]);
	    }
	    SimpleDateFormat df = new SimpleDateFormat("yyyyMMdd.HHmmss.SSS");
	    my_out.write("\n client ipaddr: " + server.socket.getInetAddress());
	    my_out.write("\n client princ : " + server.getClientIdentity());
	    my_out.write("\n server princ : " + server.getServerIdentity());
	    Calendar now = Calendar.getInstance();
	    my_out.write("\n time is      : " + mytime(now.getTime()) +  " (" +  df.format(now.getTime()) + ")");
	    my_out.write("\n this is just some more output\n");
	    my_err.write("This error message contains : just for fun\n");
	    server.make_out(my_out.getBuffer().toString());
	    server.make_err(my_err.getBuffer().toString());
	    if (args[0].startsWith("rc") && args.length > 1)
		return Integer.parseInt(args[1]);
	    return 0;
	}
    }

	/* this does the housekeeping to set up a server
	 * instance.  The most important thing is fetching
	 * the service key from the keytab.
	 * This needs to run with Djavax.security.auth.useSubjectCredsOnly=false
	 * so that this actually works.
	 *
	 * In this test case, all requests
	 * get done in one thread.  Non-trivial requests
	 * ought to be done on separate threads.
	 */
    public static void main(String[] args)
	throws IOException, GSSException {

        if (args.length != 2) {
System.err.println(" args is " + args.length + " not 3");
            System.err.println("Usage: java <options> t7 "
                               + " portno service_princ");
            System.exit(-1);
        }

	int localPort = Integer.parseInt(args[0]);

	ServerSocket ss = new ServerSocket(localPort);
	GSSManager manager = GSSManager.getInstance();

	/* get server credentials */
	Oid krb5Mechanism = new Oid("1.2.840.113554.1.2.2");
	Oid krb5PrincipalNameType = new Oid("1.2.840.113554.1.2.2.1");
	GSSName serverName = manager.createName(args[1],
	    krb5PrincipalNameType);
	GSSCredential serverCreds = manager.createCredential(serverName,  
	    GSSCredential.INDEFINITE_LIFETIME,
	    krb5Mechanism,
	    GSSCredential.ACCEPT_ONLY);

	/* XXX should start a separate thread to process each request */
	while (true) {
	    Socket socket = ss.accept();

	    RemctlServer server = new RemctlServer(socket, serverCreds);
	    server.serve_a_client(new t7_servlet());
	    socket.close();
	}
    }
}

/*
**  Local variables:
**  java-basic-offset: 4
**  indent-tabs-mode: nil
**  end:
*/
