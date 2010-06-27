-- Changelog:
--
-- 5 April 2009 -> pquimby created initial version
--

-- Usage:
--  This script will set the volume of gutenbach (assuming you have remctl) to your iTunes volume scaled to the max value of 31 (which is the max volume for gutenbach at the time this script was written).

-- Ex:// If your iTunes volume is set at 50% then you will set the gutenbach volume to .50*31 or roughly 15.

tell application "iTunes"
	set vol to (sound volume * 31 / 100)
end tell

set command to "/usr/local/bin/remctl hostname volume set " & vol
do shell script command