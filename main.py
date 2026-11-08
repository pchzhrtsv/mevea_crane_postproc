"""Compare pump power for two cases from the current source dataset."""
import matplotlib.pyplot as plt

from utils.paths import DATA_DIR
from utils.plot_blocks import power_plots
from utils.processing import start_from
from utils.result_parser import load_specific_results


# Cases available in commitable_data: lightening, payload, pressure code.
CASES = [(0, 400, 30), (30, 400, 30)]


def main():
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["mathtext.fontset"] = "stix"

    datasets = load_specific_results(DATA_DIR, CASES)
    cutted_datasets = start_from(datasets, 2.4)
    power_plots(cutted_datasets, cases=CASES)


if __name__ == "__main__":
    main()
