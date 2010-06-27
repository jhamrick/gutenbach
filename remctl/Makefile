all:

install:
	mkdir -p $(DESTDIR)/usr/lib/gutenbach/remctl/
	mkdir -p $(DESTDIR)/etc/remctl/conf.d/
	install -m 755 lib/gutenbach/* $(DESTDIR)/usr/lib/gutenbach/remctl/
	install -m 755 lib/remctl/* $(DESTDIR)/etc/remctl/conf.d/
