#!/usr/bin/perl -w
#
# Test default parameters against Stanford's NetDB service.
#
# This test can only be run by someone local to Stanford with appropriate
# access to the NetDB role server and will be skipped in all other
# environments.  We need to use a known service running on the standard ports
# in order to test undefined values passed to Net::Remctl functions.
#
# Written by Russ Allbery
# Copyright 2008 Board of Trustees, Leland Stanford Jr. University
#
# See LICENSE for licensing terms.

BEGIN { our $total = 6 }
use Test::More tests => $total;

use Net::Remctl;

my $netdb = 'netdb-node-roles-rc.stanford.edu';
my $host  = 'windlord.stanford.edu';
my $user  = 'rra';

# Determine the local principal.
my $klist = `klist 2>&1` || '';
SKIP: {
    skip "tests useful only with Stanford Kerberos tickets", $total
        unless $klist =~ /^Default principal: \S+\@stanford\.edu$/m;
    my $remctl = Net::Remctl->new;
    isa_ok ($remctl, 'Net::Remctl', 'Object creation');

    # We want to test behavior in the presence of explicitly undefined values,
    # so suppress the warnings.
    no warnings 'uninitialized';
    ok ($remctl->open($netdb, undef, undef),
        'Connection with explicit undef');
    undef $remctl;
    $remctl = Net::Remctl->new;
    my $port = undef;
    my $principal = undef;
    ok ($remctl->open($netdb, $port, $principal),
        'Connection with implicit undef');
    ok ($remctl->command('netdb', 'node-roles', $user, $host),
        'Sending command');
    my ($output, $roles);
    my $okay = 1;
    do {
        $output = $remctl->output;
        if ($output->type eq 'output') {
            if ($output->stream == 1) {
                $roles .= $output->data;
            } elsif ($output->stream == 2) {
                print STDERR $output->data;
                $okay = 0;
            }
        } elsif ($output->type eq 'error') {
            warn $output->error, "\n";
            $okay = 0;
        } elsif ($output->type eq 'status') {
            $okay = 0 unless $output->status == 0;
        } else {
            die "Unknown output token from library: ", $output->type, "\n";
        }
    } while ($output->type eq 'output');
    ok ($okay, 'Reading output');
    is ($roles, "admin\nuser\n", 'Saw correct output');
}
