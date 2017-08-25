# hdfs-audit-parser
Perl script that accepts a path to an HDFS audit log file and creates an [SQLite](https://www.sqlite.org/) database file with a single table named `audit`. Each audit log line is parsed as a set of key-value pairs with the keys as columns in the `audit` table.

## Usage
    hdfs-audit-parser [--db dbFile] audit-log-file

If dbFile is specified then records are loaded into the existing database file. Else a new database file is created under `/tmp`.

## Example Usage

### Loading records
    $ hdfs-audit-parser hdfs-audit.log
    >> Opened Database /tmp/audit-4662259.db
    >> Imported 1607875 total records

### Get the top 5 users
    $ sqlite3 /tmp/audit-4662259.db 'select ugi,count(*) as thecount from audit group by ugi order by thecount DESC';
    mapred|1595240
    hive|11024
    spark|610
    yarn|516
    nagios|246

### Get the top 5 commands
    $ sqlite3 /tmp/audit-4662259.db 'select cmd,count(*) as thecount from audit group by cmd order by thecount DESC limit 5'
    getfileinfo|1111915
    open|168865
    create|160012
    mkdirs|157074
    listStatus|5959


### Get the top 5 most active times, grouped by seconds.
    $ sqlite3 /tmp/audit-4662259.db 'select time,count(*) as thecount from audit group by time order by thecount DESC limit 5'
    2015-12-30 16:52:23|2413
    2015-12-30 16:47:13|1640
    2015-12-30 16:52:22|1213
    2015-12-30 16:27:08|1211
    2015-12-30 16:17:21|1154

### Count the number of read requests.
    $ sqlite3 /tmp/audit-4662259.db "select count(*) from audit where cmd in ('checkAccess', 'contentSummary', 'getAclStatus', 'getEZForPath', 'getfileinfo', 'listStatus', 'open', 'listEncryptionZones')"
    1486527

### Count the number of write requests.
    $ sqlite3 /tmp/audit-4662259.db "select count(*) from audit where cmd in ('append', 'create', 'delete', 'mkdirs', 'rename', 'setOwner', 'setPermission', 'setReplication', 'setTimes')"
    121348

Makes use of Perl's [DBD::SQLite module](http://search.cpan.org/~msergeant/DBD-SQLite-0.31/lib/DBD/SQLite.pm) and the Perl [DBI module](http://search.cpan.org/~timb/DBI-1.634/DBI.pm).
