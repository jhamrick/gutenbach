/*  t 5
**
**  This is a test java client for RemctlClient.
**  This is intended to model the behavior of a hypothetical
**  web application which wants to see if somebody is eligible
**  to have their password reset, and if so, reset it and maybe
**  do something with the password.  As such, it illustrates the
**  use of "keepalive" to run 2 remctl commands on one connection,
**  checking the exit code of a remctl command, and
**  capturing and parsing the output from a remctl command,
**  meanwhile passing error output straight on to stderr.
**
**  Written by Marcus Watts <mdw@umich.edu>
**  July, 2007
*/

import javax.security.auth.callback.*;
import javax.security.auth.login.*;
import javax.security.auth.Subject;
import com.sun.security.auth.callback.TextCallbackHandler;
import org.ietf.jgss.*;

import java.net.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.Iterator;
import java.nio.ByteBuffer;
import java.security.PrivilegedExceptionAction;

import org.eyrie.eagle.remctl.*;

public class t5 {
    /**
     * Main should be invoked as follows:
     * <p>
     * <code>java -Djava.security.auth.login.config=login.conf t5 {host} {loginid} {otid} [ {newpassword} ]</code>
     *
     */

    public static void main(String[] args) {

        if (args.length < 3 || args.length > 4) {
            System.err.println("Usage: java <options> t5 "
                               + " <hostName> login otid [newpass]");
            System.exit(1);
        }


	try {
	    final LoginContext lc = new LoginContext(Remctl.DEFAULT_NAME,
		    new TextCallbackHandler());
	    lc.login();
	    try {
		StringBuffer x;
		final String host = args[0];
		nv_parse nv;
			/* build up command vectors */
		String query[] = new String[4];
		String reset[] = new String[args.length + 1];
		query[0] = "opw"; reset[0] = "opw";
		query[1] = "query"; reset[1] = "reset";
		query[2] = args[1]; reset[2] = args[1];	/* login */
		query[3] = args[2]; reset[3] = args[2];	/* otid */
		if (args.length == 4)
				    reset[4] = args[3];
		StringWriter my_out = new StringWriter();
		PrintWriter my_err = new PrintWriter(System.err, true);

		    /* setup.  make my RemctlClient */
		RemctlClient rc = new RemctlClient(host, 0,
			null, my_out, my_err, lc);

		    /* run the query.  Look for name value pairs in output,
		     * opw is expected to output:
		     *  lastactive: 0
		     * Discard output after printing/parsing.
		     */
		rc.process(query);
		x = my_out.getBuffer();
		System.out.print(x);
		nv = new nv_parse(x.toString());
		x.setLength(0);
		while (nv.more()) {
    System.out.println("key=<" + nv.key + "> value=<" + nv.value + ">");
		}

		    /* conditionally run the reset.  Look for more name
		     * value pairs in output.  opw is expected to output:
		     *  new password: garglefoo:blorp
		     */
		if (0 == rc.getReturnCode())
		    rc.process(reset);
		rc.finishup();
		x = my_out.getBuffer();
		System.out.print(x);
		nv = new nv_parse(x.toString());
		while (nv.more()) {
    System.out.println("key=<" + nv.key + "> value=<" + nv.value + ">");
		}

		System.exit(rc.getReturnCode());
	    } catch (Exception e) {
		e.printStackTrace();
		System.exit(99);
	    } finally {
		lc.logout();
	    }
	} catch (Exception e) {
	    e.printStackTrace();
	    System.exit(99);
	}
    }

    /* helper class.  Eat a string that is expected
     * to contain newline terminated lines containing
     * keyword : value pairs
     * ignores any lines that don't contain :
     *  XXX this should be an Iterator
     */
    static class nv_parse {
	private String key, value;
	String lines[];
	int dot;
	public nv_parse(String s) {
	    lines = s.split("\n", 0);
	    dot = 0;
	}
	/* advance to the next word pair. */
	public boolean more() {
	    for (; dot < lines.length; ++dot) {
		String wordpair[] = lines[dot].split(": ", 2);
		if (wordpair.length != 2) continue;
		key = wordpair[0].trim();
		value = wordpair[1].trim();
		++dot;
		return true;
	    }
	    return false;
	}
	public String key () {
	    return key;
	}
	public String value() {
	    return value;
	}
    }
}

/*
**  Local variables:
**  java-basic-offset: 4
**  indent-tabs-mode: nil
**  end:
*/
