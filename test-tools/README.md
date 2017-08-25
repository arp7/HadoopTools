# Test Utilities

## datanode-block-injector
Perl script that can inject block files into the storage directories of a running DataNode. This is useful for testing the system with millions of block files. The script accepts paths to an existing block and meta file which will be used as templates.

The injected blocks will be picked up by the DataNode directory scanner eventually. However the scanner runs once every 6 hours by default so you may either restart the DataNode or set `dfs.datanode.directoryscan.interval` to something shorter to make the blocks visible more quickly.

## Usage

    datanode-block-injector --bpid <bpid> --numblocks <num-blocks>
        --startblockid <starting-block-id> --storagedirs <dir1;dir2;...;dirN>
        --blockfile <template-block-file> --metafile <template-meta-file>
        [--genstamp <genstamp>]

    The default genstamp is 1000. All other parameters are required.

    Template block and meta files can be generated from an existing cluster.
    There is no blocklength parameter as the block length will be the same as
    the size of the template-block-file.


