-- -----------------
-- iTunes -> sipbmp3
-- -----------------
-- This is a simple little script which sends
-- music from an iTunes library to the sipbmp3
-- lpr server.
--
-- Changelog:
--
-- 9 Jan 2009 -> price added 'quoted form'
-- 7 Jan 2009 -> kmill created initial version
--
-- Installation:
--
-- 1) Launch the Printer Setup Utility and add
--    an IP Printer with the LPD protocol with
--    the following information:
--     Address: zygorthian-space-raiders.mit.edu
--     Queue: sipbmp3
--    It is not necessary to specify the driver.
--
-- 2) Create the directory ~/Library/iTunes/Scripts
--    and place the "Send to sipbmp3.scpt" file
--    within.
--
-- Usage:
--
-- When in iTunes, select the songs which you
-- would like to hear in the office, and click
-- "Send to sipbmp3" in the script menu from
-- the menu bar.  The script menu looks like a
-- little scroll icon.  There will be no
-- feedback beyond the pleasant sounds you now
-- hear around you.

set lista to {}

tell application "iTunes"
	repeat with t in selection
		if class of t is (file track) then
			set loc to POSIX path of (get location of t)
			set end of lista to "lpr -o raw -Psipbmp3 " & (quoted form of loc)
		end if
	end repeat
end tell

repeat with com in lista
	do shell script com
end repeat