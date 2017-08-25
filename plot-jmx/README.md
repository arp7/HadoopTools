# plot-jmx.py
Python script to generate a plot of a numeric metric value over time from a series of JSON files. This can be useful in environments where Grafana is not available for visualizing metrics.

## Usage

    plot-jmx.py -i <input-files-pattern> [-o output-file.csv] <metricSpec1:counter> [<metricSpec2:rate>] ...

Each input file is a JSON dump of the JMX metrics from a Hadoop service. Each filename should be the corresponding UNIX epoch.

e.g. A JSON dump of the NameNode JMX can be obtained with:

    curl -o $(date "+%s") "http://<NameNodeIpAddress>:50070"

Each metric must be specified as a beanName:metricName:type, where type is either 'rate' or 'counter'.

A metric spec can also be specified as `beanName1:metricName1+beanName2:metricName2:type` in which case the counts will be summed.

### Example Usage

1. Plot `getFileInfo_num_ops` vs. elapsed time.
```
plot-jmx.py -i "/inputfiles/*" Hadoop:service=NameNode,name=RpcDetailedActivityForPort8020:getFileInfo_num_ops:counter
```
1. Plot sum of port 8020 RPC processing time and RPC queue time vs. elapsed time.
```
plot-jmx.py -i "/inputfiles/*" Hadoop:service=NameNode,name=RpcActivityForPort8020:RpcQueueTime_avg_time+Hadoop:service=NameNode,name=RpcActivityForPort8020:RpcProcessingTime_avg_time:rate
```

