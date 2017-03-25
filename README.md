# HadoopTools
Tools for Debugging Hadoop Clusters

## hdfs-audit-parser
Perl script that accepts a path to an HDFS audit log file and creates an [SQLite](https://www.sqlite.org/) database file with a single table named `audit`. Each audit log line is parsed as a set of key-value pairs with the keys as columns in the `audit` table.

### Usage
    hdfs-audit-parser [--db dbFile] audit-log-file

If dbFile is specified then records are loaded into the existing database file. Else a new database file is created under `/tmp`.

### Example Usage

#### Loading records
    $ hdfs-audit-parser hdfs-audit.log
    >> Opened Database /tmp/audit-4662259.db
    >> Imported 1607875 total records

#### Get the top 5 users
    $ sqlite3 /tmp/audit-4662259.db 'select ugi,count(*) as thecount from audit group by ugi order by thecount DESC';
    mapred|1595240
    hive|11024
    spark|610
    yarn|516
    nagios|246

#### Get the top 5 commands
    $ sqlite3 /tmp/audit-4662259.db 'select cmd,count(*) as thecount from audit group by cmd order by thecount DESC limit 5'
    getfileinfo|1111915
    open|168865
    create|160012
    mkdirs|157074
    listStatus|5959


#### Get the top 5 most active times, grouped by seconds.
    $ sqlite3 /tmp/audit-4662259.db 'select time,count(*) as thecount from audit group by time order by thecount DESC limit 5'
    2015-12-30 16:52:23|2413
    2015-12-30 16:47:13|1640
    2015-12-30 16:52:22|1213
    2015-12-30 16:27:08|1211
    2015-12-30 16:17:21|1154

Makes use of Perl's [DBD::SQLite module](http://search.cpan.org/~msergeant/DBD-SQLite-0.31/lib/DBD/SQLite.pm) and the Perl [DBI module](http://search.cpan.org/~timb/DBI-1.634/DBI.pm).


## datanode-block-injector
Perl script that can inject block files into the storage directories of a running DataNode. This is useful for testing the system with millions of block files. The script accepts paths to an existing block and meta file which will be used as templates.

The injected blocks will be picked up by the DataNode directory scanner eventually. However the scanner runs once every 6 hours by default so you may either restart the DataNode or set `dfs.datanode.directoryscan.interval` to something shorter to make the blocks visible more quickly.

### Usage

    datanode-block-injector --bpid <bpid> --numblocks <num-blocks>
        --startblockid <starting-block-id> --storagedirs <dir1;dir2;...;dirN>
        --blockfile <template-block-file> --metafile <template-meta-file>
        [--genstamp <genstamp>]

    The default genstamp is 1000. All other parameters are required.

    Template block and meta files can be generated from an existing cluster.
    There is no blocklength parameter as the block length will be the same as
    the size of the template-block-file.


## plot-jmx.py
Python script to generate a plot of a numeric metric value over time from a series of JSON files. This can be useful in environments where Grafana is not available for visualizing metrics.

### Usage

    plot-jmx.py -i <input-files-pattern> [-o output-file.csv] <metricSpec1:counter> [<metricSpec2:rate>] ...

Each input file is a JSON dump of the JMX metrics from a Hadoop service. Each filename should be the corresponding UNIX epoch.

e.g. A JSON dump of the NameNode JMX can be obtained with:

    curl -o $(date "+%s") "http://<NameNodeIpAddress>:50070"

Each metric must be specified as a beanName:metricName:type, where type is either 'rate' or 'counter'.

A metric spec can also be specified as `beanName1:metricName1+beanName2:metricName2:type` in which case the counts will be summed.

#### Example Usage

1. Plot `getFileInfo_num_ops` vs. elapsed time.
```
plot-jmx.py -i "/inputfiles/*" Hadoop:service=NameNode,name=RpcDetailedActivityForPort8020:getFileInfo_num_ops:counter
```
1. Plot sum of port 8020 RPC processing time and RPC queue time vs. elapsed time.
```
plot-jmx.py -i "/inputfiles/*" Hadoop:service=NameNode,name=RpcActivityForPort8020:RpcQueueTime_avg_time+Hadoop:service=NameNode,name=RpcActivityForPort8020:RpcProcessingTime_avg_time:rate
```

