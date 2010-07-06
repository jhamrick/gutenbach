--TEST--
Check full remctl API
--SKIPIF--
<?php
    if (!file_exists("remctl-test.pid"))
        echo "skip remctld not running";
?>
--FILE--
<?php
    $fh = fopen("remctl-test.princ", "r");
    $principal = rtrim(fread($fh, filesize("remctl-test.princ")));
    $r = remctl_new();
    if ($r == null) {
        echo "remctl_new failed\n";
        exit(2);
    }
    echo "Created object\n";
    if (!remctl_open($r, "localhost", 14373, $principal)) {
        echo "remctl_open failed\n";
        exit(2);
    }
    echo "Opened connection\n";
    $args = array("test", "test");
    if (!remctl_command($r, $args)) {
        echo "remctl_command failed\n";
        exit(2);
    }
    echo "Sent command\n";
    $output = remctl_output($r);
    echo "1: $output->type\n";
    echo "1: (stream $output->stream) $output->data\n";
    $output = remctl_output($r);
    echo "2: $output->type\n";
    echo "2: $output->status\n";
    $output = remctl_output($r);
    echo "3: $output->type\n";

    $args = array("test", "status", "2");
    if (!remctl_command($r, $args)) {
        echo "remctl_command failed\n";
        exit(2);
    }
    echo "Sent status command\n";
    $output = remctl_output($r);
    echo "1: $output->type\n";
    echo "1: $output->status\n";

    $args = array("test", "bad-command");
    if (!remctl_command($r, $args)) {
        echo "remctl_command failed\n";
        exit(2);
    }
    echo "Sent bad command\n";
    $output = remctl_output($r);
    echo "1: $output->type\n";
    echo "1: $output->data\n";
    echo "1: $output->error\n";
    remctl_close($r);
?>
--EXPECT--
Created object
Opened connection
Sent command
1: output
1: (stream 1) hello world

2: status
2: 0
3: done
Sent status command
1: status
1: 2
Sent bad command
1: error
1: Unknown command
1: 5
