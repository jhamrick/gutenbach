all:

install:
	mkdir -p $(DESTDIR)/usr/lib/gutenbach/remctl/
	mkdir -p $(DESTDIR)/etc/remctl/conf.d/
	install -m 755 lib/gutenbach/cd-* $(DESTDIR)/usr/lib/gutenbach/remctl/
	install -m 755 lib/gutenbach/status-* $(DESTDIR)/usr/lib/gutenbach/remctl/
	install -m 755 lib/gutenbach/volume-* $(DESTDIR)/usr/lib/gutenbach/remctl/
	install -m 644 lib/gutenbach/voldaemon.c $(DESTDIR)/usr/lib/gutenbach/remctl/
	install -m 644 lib/remctl/* $(DESTDIR)/etc/remctl/conf.d/

clean:
