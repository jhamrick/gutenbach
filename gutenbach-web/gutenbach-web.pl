use Net::CUPS;
use Net::CUPS::Destination;
use Image::ExifTool qw(ImageInfo);
use CGI ':standard';

use strict;
use warnings;

my $cups = Net::CUPS->new();

my $printer = $cups->getDestination("buildsmp3");
#print header();
print start_html();
my @jobs = $printer->getJobs( 0, 0 );
my $job_ref;
my $jobid;
my $attr;
print  <<EOF;
<TABLE SUMMARY="Job List"> 
<THEAD> 
<TR><TH> USER</TH><TH>TITLE</TH><TH>ARTIST</TH><TH>ALBUM</TH></TR> 
</THEAD>
<TBODY>  
EOF
foreach $jobid(@jobs) 
{       
	$job_ref = $printer->getJob($jobid);
	#print "$job_ref->{ 'id' }\t\t$job_ref->{ 'user'}\t\t$job_ref->{ 'title' }\n";
	my $filepath = "/var/spool/cups/d00$job_ref->{ 'id' }-001";
	my $fileinfo = ImageInfo($filepath);
	my $magic = $fileinfo->{FileType};
	#print"$job_ref->{ 'user' } is playing:\n";
	print "<TR VALIGN=\"TOP\">";
	print "<TD>$job_ref->{ 'user'}</TD>\n";
	if($magic)
	{
	   # print "MAGIC";
	    if (exists $fileinfo->{'Title'}) {
		printf("<TD>%s</TD>\n", $fileinfo->{'Title'});
	    }
	    foreach my $key (qw/Artist Album AlbumArtist/) {
		if (exists $fileinfo->{$key}) {
		    printf("<TD>%s</TD>\n", $fileinfo->{$key}) if exists $fileinfo->{$key};
		    
		}
	    }
	}
	else
	{
	    print "<TD>$job_ref->{ 'title' }</TD><TD></TD><TD></TD> \n";
	}
	print "</TR>";

}
print "</TBODY>\n</TABLE>";
	
print end_html();	    
