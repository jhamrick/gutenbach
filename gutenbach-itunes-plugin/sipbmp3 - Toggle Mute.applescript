-- -----------------
-- iTunes -> sipbmp3
-- -----------------

-- Changelog:
-- 10 Nov 2009 -> pquimby created initial version

-- Installation:
-- For installation instructions see the INSTALL file in the snippets/sipbmp3-iTunes folder--

-- Usage:
--
-- Running this script will toggle the mute on sipbmp3 on or off.

tell application "iTunes"
	set vol to sound volume
end tell

set command to "/usr/local/bin/remctl zsr volume set " & vol
do shell script command