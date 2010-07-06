--TEST--
Check for remctl module
--FILE--
<?php if (extension_loaded("remctl")) echo "remctl module is available"; ?>
--EXPECT--
remctl module is available
