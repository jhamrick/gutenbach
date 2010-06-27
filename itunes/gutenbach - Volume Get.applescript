-- ------------------
-- iTunes -> gutenbach
-- ------------------

-- Changelog:
--
-- 10 Oct 2009 -> pquimby created initial version
--

--For installation instructions see the INSTALL file in the snippets/sipbmp3-iTunes folder

-- Usage:
--  This script will get the volume of gutenbach and put it on your iTunes volume scaled to the max value of 31 (which is the max volume for gutenbach at the time this script was written).


tell application "iTunes"
	set currentVolume to (do shell script "/usr/local/bin/remctl hostname volume get")
	set currentVolume to currentVolume / 31 * 100
	set the sound volume to currentVolume
end tell