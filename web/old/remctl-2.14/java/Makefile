# Makefile for Java remctl implementation.
#
# This Makefile is not (yet) integrated with the rest of the remctl build
# system.  You will need to either edit the JDK setting below or override it
# on the command line with:
#
#     make JAVA_HOME=/path/to/jdk/directory
#
# Currently, only the Sun Java JDK is supported (1.4.2, 5, or 6).
#
# Originally written by Marcus Watts <mdw@umich.edu>
# Copyright 2007 Marcus Watts
# Copyright 2007, 2008 Board of Trustees, Leland Stanford Jr. University
#
# See LICENSE for licensing terms.

JAVA_HOME ?= /usr/lib/jvm/java-6-sun
JAVAC      = $(JDK)/bin/javac
JAR        = $(JDK)/bin/jar

ORIGIN     = org/eyrie/eagle/remctl
SOURCE     = $(ORIGIN)/RemctlClient.java $(ORIGIN)/RemctlServer.java \
	     $(ORIGIN)/Remctl.java
CLASS	   = $(SOURCE:.java=.class)

all: remctl.jar t5.class t7.class

t5.class: t5.java $(CLASS)
	$(JAVAC) -g t5.java

t7.class: t7.java $(CLASS)
	$(JAVAC) -g t7.java

remctl.jar: $(CLASS)
	$(JAR) cfe remctl.jar $(ORIGIN)/RemctlClient $(ORIGIN)/*.class

$(ORIGIN)/RemctlClient.class: $(ORIGIN)/RemctlClient.java $(ORIGIN)/Remctl.class
	$(JAVAC) -g $(ORIGIN)/RemctlClient.java

$(ORIGIN)/RemctlServer.class: $(ORIGIN)/RemctlServer.java $(ORIGIN)/Remctl.class
	$(JAVAC) -g $(ORIGIN)/RemctlServer.java

$(ORIGIN)/Remctl.class: $(ORIGIN)/Remctl.java
	$(JAVAC) -g $(ORIGIN)/Remctl.java

clean:
	rm -rf $(ORIGIN)/*.class remctl.jar *.class
