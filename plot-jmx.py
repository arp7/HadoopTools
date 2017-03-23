#!/usr/bin/env python3

from collections import OrderedDict
from enum import Enum
from os.path import basename
import glob
import matplotlib.pyplot as plt
import sys
import getopt


# ---------------------------------------------------------------------------
# Class definitions.
#
class MetricType(Enum):
    COUNTER = 1
    RATE = 2


# A class to Store information about a counter.
class Metric:
    def __init__(self, name, metric_type):
        self.name = name
        self.values = []
        self.values_for_plot = []
        self.metric_type = metric_type
        # Is the metric a sum of two or more.
        self.is_sum = '+' in name


# ----------------------------------------------------------------------------
# Methods
#
def usage_and_die():
        print('''
        Usage: plot-jmx.py -i <input-files-pattern> [-o output-file.csv]
                              <metric1:counter> [<metric2:rate>] ...

            Plot one or more metrics over time from multiple JMX files

            It is assumed that each file is a single JMX dump and each filename
            should be the corresponding UNIX epoch.

            Each metric must be specified as a name:type, where type is
            either 'rate' or 'counter'.

            A metric spec can also be specified as 'name1+name2:type' in which
            case the counts will be summed.
            ''')
        sys.exit()


def parse_args(input_args):
    """
    Parse the supplied command-line arguments and return the input file glob
    and metric spec strings.

    :param input_args: Command line arguments.
    :return: A triplet, the first element of which is the input file glob,
             the second element is the output file name (may be empty),
             the third element is a list of metric spec strings.
    """
    file_glob = ""
    output_file_name = ""
    try:
        opts, args = getopt.getopt(input_args, "hi:o:")
    except getopt.GetoptError as err:
        print(str(err))
        usage_and_die()

    for o, a in opts:
        if o == "-h":
            usage_and_die()
        elif o == "-i":
            file_glob = a
        elif o == "-o":
            output_file_name = a
        else:
            usage_and_die()
    if not file_glob:
        usage_and_die()

    return file_glob, output_file_name, args


def parse_metric_specs(spec_strings):
    """
    Parse the metric specs provided as a list of strings and return an
    OrderedDict of Metric objects. Each metric spec string is specified
    as "name:MetricType".
    """
    parsed_metrics = OrderedDict()
    for metric_spec in spec_strings:
        if ":" not in metric_spec:
            print("ERROR: Metric must be specified as 'name:type'")
            sys.exit()
        name, metric_type = metric_spec.split(":")
        parsed_metrics[name] = Metric(name, MetricType[metric_type.upper()])
    return parsed_metrics


def get_raw_metrics_from_file(filename):
    """
    Parse all metrics as 'name : value' pairs from the given file and return
    a dictionary of the metrics.

    TODO: The file must be parsed as JSON.
    """
    seen_metrics = {}
    with open(filename) as mf:
        lines = mf.readlines()
    print("Read {} lines from {}".format(len(lines), filename))
    for line in lines:
        try:
            if ":" in line:
                metric_name, metric_val = line.split(":", 1)
                metric_name = metric_name.strip().replace("\"", "")
                seen_metrics[metric_name] = float(metric_val.strip().replace(",", ""))
        except ValueError:
            continue
    return seen_metrics


def update_metrics_map(metrics_map, raw_metrics):
    """
    Update a dictionary of Metric objects with metric values parsed from
    a single file. Handles compound Metrics which can be a sum of two or
    more metrics.

    :param metrics_map: Dictionary of Metric objects to be updated.
    :param raw_metrics: Dictionary of metrics parsed from a single JSON file.
    :return: True on success, False on failure.
    """
    try:
        for metric in metrics_map.values():
            value = 0
            if not metric.is_sum:
                value = raw_metrics[metric.name]
            else:
                for component in metric.name.split("+"):
                    value += raw_metrics[component]
            metric.values.append(value)
            print("Saved metric value: {}={}".format(metric.name, value))
            return True
    except KeyError:
        # Ignore the file if any metric was missing.
        return False


def generate_relative_epochs(epochs):
    relative = []
    for i in range(0, len(epochs)):
        relative.append(epochs[i] - epochs[0])
    return relative


def plot_graph(epochs, metrics_map):
    """
    Generate a plot of the given metrics.

    :param epochs: A list of relative epochs.
    :param metrics_map: Dictionary of Metric objects to be plotted.
    """
    if len(metrics_map) > 1:
        print("WARN: Not generating plot. Multi-line plots not supported yet")
        return

    # colors = ['b', 'g', 'r', 'c', 'm', 'k', 'y']
    for s in metrics_map.values():
        points_to_plot = min(len(epochs), len(s.values_for_plot))
        print("Plotting {} values".format(points_to_plot))
        plt.plot(epochs[:points_to_plot], s.values_for_plot[:points_to_plot],
                 "b-", label=s.name)
        break

    plt.xlabel("Seconds elapsed")
    plt.legend()
    plt.show()


def parse_metric_vals_and_epochs_from_files(file_glob, metrics_map):
    """
    Parse JSON files described by the given glob.
    :param file_glob: Glob describing the input JSON files.
    :param metrics_map: Dictionary of Metrics objects to be updated.
    :return: A list of epochs, read from the file names.
    """
    # Parse out the metric values from each file.
    # The file name should be the UNIX epoch.
    #
    epochs = []
    for jmx_file_name in glob.glob(file_glob):
        metrics_from_file = get_raw_metrics_from_file(jmx_file_name)
        if update_metrics_map(metrics_map, metrics_from_file):
            epochs.append(int(basename(jmx_file_name)))
    return epochs


def process_metrics_data(epochs, metrics_map, output_file_name):
    """

    :param epochs: A list of all the UNIX epochs, one corresponding to each
                   raw metric value.
    :param metrics_map: A dictionary of Metrics objects with raw values.
    :param output_file_name: File to which the processed data will be written in
                        csv format.
    :return:
    """
    # Open the output file and write the header.
    if output_file_name:
        f = open(output_file_name, 'w')
        f.write("Seconds Elapsed, {}\n".format(", ".join(metrics_map.keys())))

    # Now process the raw values of the metrics.
    relative_epochs = [0]

    for i, current_epoch in enumerate(epochs):
        if i > 0:
            relative_epochs.append(current_epoch - epochs[0])

        values_for_csv = []
        for m in metrics_map.values():
            print("Iter={}, Value of {}={}".format(
                i + 1, m.name, m.values[i]))
            # If it's a counter, then compute its rate.
            if m.metric_type == MetricType.COUNTER:
                curr_count = m.values[i]
                if i > 0:
                    delta = max(curr_count - m.values[i - 1], 0)
                    epoch_delta = current_epoch - epochs[i - 1]
                    m.values_for_plot.append(delta / epoch_delta)
                    values_for_csv.append(delta / epoch_delta)
                else:
                    # The rate at the first epoch is unknowable, just set it
                    # it to zero.
                    m.values_for_plot.append(0)
                    values_for_csv.append(0)
            else:
                # For a rate, there is nothing to do.
                m.values_for_plot.append(m.values[i])
                values_for_csv.append(m.values[i])

        if output_file_name:
            f.write("{},{}\n".format(
                current_epoch - epochs[0], ",".join(map(str, values_for_csv))))

    if output_file_name:
        f.close()

# ----------------------------------------------------------------------------
#


def main():
    input_file_glob, output_file, metric_specs = parse_args(sys.argv[1:])
    metrics = parse_metric_specs(metric_specs)
    all_epochs = parse_metric_vals_and_epochs_from_files(input_file_glob, metrics)
    process_metrics_data(all_epochs, metrics, output_file)
    plot_graph(generate_relative_epochs(all_epochs), metrics)


if __name__ == "__main__":
    main()
