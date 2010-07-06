--TEST--
Check simplified remctl API
--SKIPIF--
<?php
    if (!file_exists("remctl-test.pid"))
        echo "skip remctld not running";
?>
--FILE--
<?php
    $fh = fopen("remctl-test.princ", "r");
    $principal = rtrim(fread($fh, filesize("remctl-test.princ")));
    $command = array("test", "test");
    $result = remctl("localhost", 14373, $principal, $command);
    echo "stdout_len: $result->stdout_len\n";
    echo "stdout: $result->stdout\n";
    echo "stderr_len: $result->stderr_len\n";
    echo "status: $result->status\n";
    flush();

    $command = array("test", "status", "2");
    $result = remctl("localhost", 14373, $principal, $command);
    echo "stdout_len: $result->stdout_len\n";
    echo "stderr_len: $result->stderr_len\n";
    echo "status: $result->status\n";
    flush();

    $command = array("test", "bad-command");
    $result = remctl("localhost", 14373, $principal, $command);
    echo "stdout_len: $result->stdout_len\n";
    echo "stderr_len: $result->stderr_len\n";
    echo "error: $result->error\n";
    echo "status: $result->status\n";
    flush();
?>
--EXPECT--
stdout_len: 12
stdout: hello world

stderr_len: 0
status: 0
stdout_len: 0
stderr_len: 0
status: 2
stdout_len: 0
stderr_len: 0
error: Unknown command
status: 0
