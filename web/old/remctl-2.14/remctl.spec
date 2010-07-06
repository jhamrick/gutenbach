%define rel %(cat /etc/redhat-release | cut -d' ' -f7)

# Use rpmbuild option "--define 'buildperl 0'" to not build the Perl module.
%{!?buildperl:%define buildperl 1}

Name: remctl
Summary: Client/server for Kerberos-authenticated command execution
Version: 2.13
Release: 1.EL%{rel}
Copyright: MIT
URL: http://www.eyrie.org/~eagle/software/remctl/
Source: http://archives.eyrie.org/software/kerberos/%{name}-%{version}.tar.gz
Group: System Environment/Daemons
Vendor: Stanford University
Packager: Russ Allbery <rra@stanford.edu>
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: krb5-devel
Distribution: EL

%ifarch x86_64
%define ldir /usr/lib64
%else
%define ldir /usr/lib
%endif

%description
remctl is a client/server protocol for executing specific commands on a
remote system with Kerberos authentication.  The allowable commands must
be listed in a server configuration file, and the executable run on the
server may be mapped to any command name.  Each command is also associated
with an ACL containing a list of Kerberos principals authorized to run
that command.

%package server
Summary: Server for Kerberos-authenticated command execution
Group: System Environment/Daemons

%description server
remctl is a client/server protocol for executing specific commands on a
remote system with Kerberos authentication.  The allowable commands must
be listed in a server configuration file, and the executable run on the
server may be mapped to any command name.  Each command is also associated
with an ACL containing a list of Kerberos principals authorized to run
that command.

This package contains the server (remctld).

%package client
Summary: Client for Kerberos-authenticated command execution
Group: Applications/Internet

%description client
remctl is a client/server protocol for executing specific commands on a
remote system with Kerberos authentication.  The allowable commands must
be listed in a server configuration file, and the executable run on the
server may be mapped to any command name.  Each command is also associated
with an ACL containing a list of Kerberos principals authorized to run
that command.

This package contains the client program (remctl) and the client libraries.

%prep
%setup -n remctl-%{version}

%build
options="--prefix=/usr --mandir=/usr/share/man --sysconfdir=/etc/remctl"
%if %{buildperl}
options="$options --enable-perl"
%endif
PATH="/sbin:/bin:/usr/sbin:$PATH" \
%configure $options
%{__make}

%install
%{__rm} -rf %{buildroot}
%makeinstall
mkdir -p %{buildroot}/etc/xinetd.d
install -c -m 0644 examples/xinetd %{buildroot}/etc/xinetd.d/remctl
mkdir -p %{buildroot}/etc/remctl/acl
mkdir -p %{buildroot}/etc/remctl/conf.d
install -c -m 0644 examples/remctl.conf %{buildroot}/etc/remctl/remctl.conf
%ifarch x86_64
if [ -d %{buildroot}/usr/lib/ ]; then
    mv %{buildroot}/usr/lib/ %{buildroot}/%{ldir}
fi
%endif
%if %{buildperl}
find %{buildroot} -name perllocal.pod -exec rm {} \;
%endif

%files client
%defattr(-, root, root, 0755)
%{_bindir}/*
%defattr(0644, root, root)
%doc NEWS README TODO
/usr/include/remctl.h
%{ldir}/libremctl.a
%{ldir}/libremctl.la
%{ldir}/libremctl.so.1.0.0
%{_mandir}/*/remctl.*
%{_mandir}/*/remctl_*
%if %{buildperl}
%{ldir}/perl5/site_perl/
%{_mandir}/*/Net::Remctl.3pm*
%endif

%files server
%defattr(-, root, root, 0755)
%{_sbindir}/*
%defattr(0644, root, root)
%doc NEWS README TODO
%{_mandir}/*/remctld.*
/etc/xinetd.d/remctl
%dir /etc/remctl/
%defattr(0640, root, root)
%config(noreplace) /etc/remctl/remctl.conf
%defattr(0755, root, root)
%dir /etc/remctl/acl/
%defattr(0750, root, root)
%dir /etc/remctl/conf.d/

%post client
/sbin/ldconfig

%post server
# If this is the first remctl install, add remctl to /etc/services and
# restart xinetd to pick up its new configuration.
if [ "$1" = 1 ] ; then
    if grep -q '^remctl' /etc/services ; then
        :
    else
        echo 'remctl    4373/tcp' >> /etc/services
    fi
    if [ -f /var/run/xinetd.pid ] ; then
        kill -HUP `cat /var/run/xinetd.pid`
    fi
fi

%postun client
/sbin/ldconfig

%postun server
# If we're the last remctl package, remove the /etc/services line and
# restart xinetd to reflect its new configuration.
if [ "$1" = 0 ] ; then
    if [ ! -f /usr/sbin/remctld ] ; then
        if grep -q "^remctl" /etc/services ; then
            grep -v "^remctl" /etc/services > /etc/services.tmp
            mv -f /etc/services.tmp /etc/services
        fi
        if [ -f /var/run/xinetd.pid ] ; then
            kill -HUP `cat /var/run/xinetd.pid`
        fi
    fi
fi

%clean
%{__rm} -rf %{buildroot}

%changelog
* Fri Nov 14 2008 Russ Allbery <rra@stanford.edu> 2.13-1
- Update for 2.13.
- PHP and Python bindings not yet supported.

* Fri Apr 4 2008 Russ Allbery <rra@stanford.edu> 2.12-1
- Update for 2.12.

* Fri Nov 9 2007 Russ Allbery <rra@stanford.edu> 2.11-1
- Update for 2.11.
- Change port configuration to 4373.

* Sun Aug 26 2007 Russ Allbery <rra@stanford.edu> 2.10-1
- Update for 2.10.
- Incorporate changes by Darren Patterson to install the Perl module.

* Sun Mar 25 2007 Russ Allbery <rra@stanford.edu> 2.7-1
- Update for 2.7.

* Sat Feb 3 2007 Russ Allbery <rra@stanford.edu> 2.6-1
- Update for 2.6.

* Sat Feb 3 2007 Russ Allbery <rra@stanford.edu> 2.5-1
- Update for 2.5.
- Incorporate changes by Darren Patterson to split into subpackages for
  client and server and remove krb5-workstation requirement.

* Wed Jan 17 2007 Russ Allbery <rra@stanford.edu> 2.4-1
- Update for 2.4.
- Changed permissions on the ACL directory to allow any user read.
- Added fix for /usr/lib64 directory on x86_64.

* Tue Aug 22 2006 Russ Allbery <rra@stanford.edu> 2.1-1
- Update for 2.1.
- Incorporate changes by Digant Kasundra and Darren Patterson to the
  Stanford-local RPM spec file, including looking for libraries in the
  correct path, creating the /etc/remctl structure, running ldconfig,
  and handling library installation properly.
- Build remctl to look in /etc/remctl/remctl.conf for its config.
- Install the examples/remctl.conf file as /etc/remctl/remctl.conf.

* Mon Aug  7 2006 Russ Allbery <rra@stanford.edu> 2.0-1
- New upstream release that now provides a library as well.
- Add TODO to documentation files.

* Fri Mar 24 2006 Russ Allbery <rra@stanford.edu> 1.12-3
- Lots of modifications based on the contributed kstart spec file.
- Use more internal RPM variables.
- Borrow the description from the Debian packages.

* Sun Feb 19 2006 Digant C Kasundra <digant@stanford.edu> 1.12-2
- Initial version.
