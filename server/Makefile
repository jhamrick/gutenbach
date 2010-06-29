all:

install:
	mkdir -p $(DESTDIR)/usr/lib/cups/backend
	mkdir -p $(DESTDIR)/usr/lib/gutenbach/inst
	mkdir -p $(DESTDIR)/usr/lib/gutenbach/rm
	install -m 755 lib/gutenbach $(DESTDIR)/usr/lib/cups/backend
	install -m 755 lib/gutenbach-get-config $(DESTDIR)/usr/lib/gutenbach/
	install -m 644 lib/README $(DESTDIR)/usr/lib/gutenbach/
	install -m 644 lib/TODO $(DESTDIR)/usr/lib/gutenbach/		
	install -m 755 inst/* $(DESTDIR)/usr/lib/gutenbach/inst/
	install -m 755 rm/* $(DESTDIR)/usr/lib/gutenbach/rm/

clean: