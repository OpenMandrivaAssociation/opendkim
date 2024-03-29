%define major 10
%define libname %mklibname opendkim
%define oldlibname %mklibname opendkim %{major}
%define devname %mklibname opendkim -d
%define tarname OpenDKIM-rel
%define tarversion 2-10-3

Summary:	A DomainKeys Identified Mail (DKIM) milter to sign and/or verify mail
Name:		opendkim
Version:	2.10.3
Release:	6
License:	BSD and Sendmail
Group:		Networking/Mail
Url:		https://github.com/trusteddomainproject/OpenDKIM
Source0:	https://github.com/trusteddomainproject/OpenDKIM/archive/refs/tags/%{tarname}-opendkim-%{tarversion}.tar.gz
Source10:	opendkim.tmpfiles
Source11:	opendkim.sysusers
Patch0:		opendkim-2.8.3-openssl-1.1.patch
BuildRequires:	sendmail-devel
BuildRequires:	pkgconfig(openssl)
BuildRequires:	dos2unix
BuildRequires:	pkgconfig(libbsd)
BuildRequires:	systemd-rpm-macros

%description
OpenDKIM allows signing and/or verification of email through an open source
library that implements the DKIM service, plus a milter-based filter
application that can plug in to any milter-aware MTA, including sendmail,
Postfix, or any other MTA that supports the milter protocol.

%package -n %{libname}
Summary:	An open source DKIM library
Group:		System/Libraries
%rename %{oldlibname}

%description -n %{libname}
This package contains a shared library for %{name}.

%package -n	%{devname}
Summary:	Development files for libopendkim
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}

%description -n %{devname}
This package contains the development files for %{name}.

%prep
%autosetup -p1 -n %{tarname}-%{name}-%{tarversion}
autoreconf -fiv

%configure \
	--disable-static \
	--enable-stats

%build
%make_build

%install
%make_install
mkdir -p %{buildroot}%{_sysconfdir}
mkdir -p %{buildroot}%{_unitdir}
dos2unix contrib/systemd/opendkim.service
install -m 0644 contrib/systemd/opendkim.service %{buildroot}%{_unitdir}/
install -D %{S:10} %{buildroot}%{_tmpfilesdir}/%{name}.conf
install -D %{S:11} %{buildroot}%{_sysusersdir}/%{name}.conf
cat > %{buildroot}%{_sysconfdir}/%{name}.conf << 'EOF'
## BASIC OPENDKIM CONFIGURATION FILE
## See opendkim.conf(5) or %{_docdir}/%{name}-%{version}/%{name}.conf.sample for more

## BEFORE running OpenDKIM you must:

## - make your MTA (Postfix, Sendmail, etc.) aware of OpenDKIM
## - generate keys for your domain (if signing)
## - edit your DNS records to publish your public keys (if signing)

## See %{_docdir}/%{name}-%{version}/INSTALL for detailed instructions.

## CONFIGURATION OPTIONS

# Specifies the path to the process ID file.
PidFile	/run/%{name}/%{name}.pid

# Selects operating modes. Valid modes are s (signer) and v (verifier). Default is v.
Mode	sv

# Log activity to the system log.
Syslog	yes

# Log additional entries indicating successful signing or verification of messages.
SyslogSuccess	yes

# If logging is enabled, include detailed logging about why or why not a message was
# signed or verified. This causes an increase in the amount of log data generated
# for each message, so set this to No (or comment it out) if it gets too noisy.
LogWhy	yes

# Attempt to become the specified user before starting operations.
UserID	%{name}:%{name}

# Create a socket through which your MTA can communicate.
Socket	inet:8891@127.0.0.1

# Required to use local socket with MTAs that access the socket as a non-
# privileged user (e.g. Postfix)
Umask	002

# This specifies a text file in which to store DKIM transaction statistics.
#Statistics	%{_localstatedir}/spool/%{name}/stats.dat

## SIGNING OPTIONS

# Selects the canonicalization method(s) to be used when signing messages.
Canonicalization	relaxed/simple

# Domain(s) whose mail should be signed by this filter. Mail from other domains will
# be verified rather than being signed. Uncomment and use your domain name.
# This parameter is not required if a SigningTable is in use.
#Domain	example.com

# Defines the name of the selector to be used when signing messages.
Selector	default

# Gives the location of a private key to be used for signing ALL messages.
KeyFile	%{_sysconfdir}/%{name}/keys/default.private

# Gives the location of a file mapping key names to signing keys. In simple terms,
# this tells OpenDKIM where to find your keys. If present, overrides any KeyFile
# setting in the configuration file. 
KeyTable	%{_sysconfdir}/%{name}/KeyTable

# Defines a table used to select one or more signatures to apply to a message based
# on the address found in the From: header field. In simple terms, this tells
# OpenDKIM how to use your keys.  
SigningTable	%{_sysconfdir}/%{name}/SigningTable

# Identifies a set of "external" hosts that may send mail through the server as one
# of the signing domains without credentials as such.
ExternalIgnoreList	refile:%{_sysconfdir}/%{name}/TrustedHosts

# Identifies a set internal hosts whose mail should be signed rather than verified.
InternalHosts	refile:%{_sysconfdir}/%{name}/TrustedHosts
EOF

mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} << 'EOF'
# Uncomment the following line to disable automatic DKIM key creation
#AUTOCREATE_DKIM_KEYS=NO
#
# Uncomment the following line to set the default DKIM selector
#DKIM_SELECTOR=default
#
# Uncomment the following to set the default DKIM key directory
#DKIM_KEYDIR=/etc/opendkim/keys
EOF

mkdir -p %{buildroot}%{_sysconfdir}/%{name}
cat > %{buildroot}%{_sysconfdir}/%{name}/SigningTable << 'EOF'
# The following wildcard will work only if
# refile:%{_sysconfdir}/%{name}/SigningTable is included
# in %{_sysconfdir}/%{name}.conf.

#*@example.com default._domainkey.example.com

# If refile: is not specified in %{_sysconfdir}/%{name}.conf, then full
# user@host is checked first, then simply host, then user@.domain (with all
# superdomains checked in sequence, so "foo.example.com" would first check
# "user@foo.example.com", then "user@.example.com", then "user@.com"), then
# .domain, then user@*, and finally *. See the opendkim.conf(5) man page
# under "SigningTable".

#example.com default._domainkey.example.com
EOF

cat > %{buildroot}%{_sysconfdir}/%{name}/KeyTable << 'EOF'
# To use this file, uncomment the #KeyTable option in %{_sysconfdir}/%{name}.conf,
# then uncomment the following line and replace example.com with your domain
# name, then restart OpenDKIM. Additional keys may be added on separate lines.

#default._domainkey.example.com example.com:default:%{_sysconfdir}/%{name}/keys/default.private
EOF

cat > %{buildroot}%{_sysconfdir}/%{name}/TrustedHosts << 'EOF'
# To use this file, uncomment the #ExternalIgnoreList and/or the #InternalHosts
# option in %{_sysconfdir}/%{name}.conf then restart OpenDKIM. Additional hosts
# may be added on separate lines (IP addresses, hostnames, or CIDR ranges).
# The localhost IP (127.0.0.1) should be the first entry in this file.
127.0.0.1
::1
EOF

install -p -d %{buildroot}%{_sysconfdir}/tmpfiles.d
cat > %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf <<'EOF'
D %{_localstatedir}/run/%{name} 0700 %{name} %{name} -
EOF

rm -r %{buildroot}%{_prefix}/share/doc/%{name}

mkdir -p %{buildroot}%{_localstatedir}/spool/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir %{buildroot}%{_sysconfdir}/%{name}/keys

install -m 0755 stats/%{name}-reportstats %{buildroot}%{_sbindir}/%{name}-reportstats
sed -i 's|^OPENDKIMSTATSDIR="/var/db/opendkim"|OPENDKIMSTATSDIR="%{_localstatedir}/spool/%{name}"|g' %{buildroot}%{_sbindir}/%{name}-reportstats
sed -i 's|^OPENDKIMDATOWNER="mailnull:mailnull"|OPENDKIMDATOWNER="%{name}:%{name}"|g' %{buildroot}%{_sbindir}/%{name}-reportstats

chmod 0644 contrib/convert/convert_keylist.sh

%pre
%sysusers_create_package %{name} %{S:11}
%tmpfiles_create_package %{name} %{S:10}

%files
%doc FEATURES KNOWNBUGS LICENSE LICENSE.Sendmail RELEASE_NOTES RELEASE_NOTES.Sendmail INSTALL
%doc contrib/convert/convert_keylist.sh %{name}/*.sample
%doc %{name}/%{name}.conf.simple-verify %{name}/%{name}.conf.simple
%doc %{name}/README contrib/lua/*.lua
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%config(noreplace) %attr(640,%{name},%{name}) %{_sysconfdir}/%{name}/SigningTable
%config(noreplace) %attr(640,%{name},%{name}) %{_sysconfdir}/%{name}/KeyTable
%config(noreplace) %attr(640,%{name},%{name}) %{_sysconfdir}/%{name}/TrustedHosts
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_unitdir}/%{name}.service
%{_sbindir}/*
%{_mandir}/*/*
%dir %attr(-,%{name},%{name}) %{_localstatedir}/spool/%{name}
%dir %attr(-,%{name},%{name}) %{_localstatedir}/run/%{name}
%dir %attr(-,root,%{name}) %{_sysconfdir}/%{name}
%dir %attr(-,root,%{name}) %{_sysconfdir}/%{name}/keys
%{_tmpfilesdir}/%{name}.conf
%{_sysusersdir}/%{name}.conf

%files -n %{libname}
%{_libdir}/libopendkim.so.%{major}*

%files -n %{devname}
%doc LICENSE LICENSE.Sendmail
%doc libopendkim/docs/*.html
%{_includedir}/%{name}
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc
