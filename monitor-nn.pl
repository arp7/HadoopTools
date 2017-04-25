#!/usr/bin/env perl

# A script that constantly checks a local NameNode process for
# responsiveness by issuing a cheap write command. If the NN
# does not respond for the specified number of seconds, issues
# a SIGQUIT (kill -3). The NN process stack dump will be available
# in its .out file.

use strict;
use warnings;

use threads;
use threads::shared;
use File::Spec;
use POSIX 'strftime';

# Epoch when the last touchz command succeeded.
# -1 if touchz has never succeeded.
my $last_success :shared = -1;


# Return the timestamp in a human-friendly format for logging.
sub get_time_for_log {
  return strftime("%Y-%m-%d %H:%M:%S%Z", localtime);
}

# Periodically send a write request to HDFS, looping forever.
sub touch_file {
  my $file_name = "/tmp/monitor-nn.safe-to-delete-this-file";
  print get_time_for_log() . " touchz using HDFS file $file_name\n";
  while (1) {
    # Update last_success if the touchz command succeeds.
    my $ret = system("hadoop", "fs", "-touchz", $file_name) >> 8;
    if ($ret == 0) {
      $last_success = time;
      print get_time_for_log() . " touchz command succeeded\n";
    } else {
      print get_time_for_log() . " touchz command failed\n";
    }
    sleep 3;
  }
}

if (scalar @ARGV != 2) {
  die "Usage: monitor-nn.pl <rpc-threshold-in-seconds> <nn-pid-file>";
}

my $threshold = $ARGV[0];
my $nn_pid_file = $ARGV[1];

if (! -e $nn_pid_file) {
  die "The PID file $nn_pid_file does not exist.";
}

# Start the monitoring thread.
my $thr = threads->create(sub { touch_file() });
print get_time_for_log() . " Starting jstack loop\n";

while (1) {
  # Compute the seconds elapsed since the last successful touchz.
  my $delta = (time - $last_success);

  if ($last_success == -1) {
    # Still waiting for the first touchz command to complete.
  } elsif ($delta >= $threshold) {
    my $nn_pid = qx(cat $nn_pid_file);
    chomp($nn_pid);
    print get_time_for_log() .
        " Delta=$delta, Threshold=$threshold, issuing \"kill -3 $nn_pid\"\n";
    system("kill", "-3", $nn_pid);
  } else {
    print get_time_for_log() .
        " Delta=$delta, Threshold=$threshold, The NameNode is responsive.\n";
  }
  sleep 10;
}

