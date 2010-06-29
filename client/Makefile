all:

install:
	mkdir -p $(DESTDIR)/usr/bin/
	install -m 755 bin/* $(DESTDIR)/usr/bin/
	gzip -9 < bin/gbq.1 > bin/gbq.1.gz
	gzip -9 < bin/gbr.1 > bin/gbr.1.gz
	gzip -9 < bin/gbrm.1 > bin/gbrm.1.gz
	gzip -9 < bin/gutenbach-client-config.1 > bin/gutenbach-client-config.1.gz
	mkdir -p $(DESTDIR)/usr/share/man/man1/
	install -m 755 bin/*.1.gz $(DESTDIR)/usr/share/man/man1/

clean:
	rm bin/*.1.gz