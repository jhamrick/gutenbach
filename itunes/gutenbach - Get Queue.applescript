-- -----------------
-- iTunes -> gutenbach
-- -----------------
-- This is a simple little script which gets the current queue on gutenbach--
-- Changelog:
--
-- 10 Oct 2009 -> pquimby created this script
--
-- Installation:
-- For installation instructions see the INSTALL file in the snippets/sipbmp3-iTunes folder--

--
-- Usage:
--
-- Run this script from iTunes

set message to (do shell script "lpq -Pgutenbach")
tell application "iTunes"
	display dialog "gutenbach currently is playing: " & "
" & message buttons "OK" default button "OK"
end tell
