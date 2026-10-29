# *google_cultivation*

1. [Overview](#overview)
2. [File contents](#file-contents)
4. [Usage examples](#usage-examples)
5. [Additional resources](#additional-resources)
6. [References](#references)

## Overview <a name="overview"></a>

This dataset is organized in a nested directory structure according to certain useful attributes of the cultivation experiments:
```
figure_dir
├── experiment_dir
│   └── ...
└── ...
```

The `figure_dir` contains subdirectories for each figure's experimental dataset (named e.g. `cultivation`, `injection`, etc). A single such dataset can be thought of as a collection of QEC data acquired in one experiment.

The `experiment_dir` contains files with information about the experiment, such as a serialized Cirq and Stim circuit, as well as the experimental results as e.g. measurement values and detection events. Below is the description of the directory contents for a single experiment instance, corresponding to a particular figure and experiment type, i.e. here `data_dir = fig2/cultivation/`:
```
data_dir
├── cirq_circuit_X.json
├── cirq_circuit_Z.json
├── stim_X.stim
├── stim_Z.stim
├── measurements.csv
├── detection_events.csv
├── corrected_observables.csv
├── raw_observables.csv
```
## File contents <a name="file-contents"></a>

Example: Figure 4, cultivation with N = 2
___
```
...
├── cirq_circuit_X(Z).json
...
```

The QEC circuit we ran for tomography X(Z) measurements, including annotations describing how detection events are computed from the measurement record and what the logical observable is. 

___
```
...
├── stim_X(Z).stim
...
```
A QEC circuit, including annotations describing how detection events are computed from the measurement record and what the logical observable is. Stored in `stim` circuit format, see [The Stim Circuit File Format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_stim_circuit.md). This circuit is modified from the cirq circuit in the following ways: 

1. Non-clifford gates are removed, and replaced with Clifford gates that make the observable values deterministic. This is useful when e.g. understanding detection regions or creating a detector error model for decoding. 
2. In our cirq circuit, we add Pauli `X` gates to echo low frequency noise. These Pauli frame changes are reversed in an additional circuit layer before each non-Clifford gate, to maintain the desired qubit evolution. In our stim circuit, for simplicity, we replace these gates with identity and tag them as `echo` for clarity. 
3. We conjugate the non-Clifford `Y` rotations by Hadamard gates (`H_YZ`), so that the physical qubit gate for the arbitrary rotation is done "virtually" (using a phase update). We tag the conjugating Hadamards with `conjugate`.

```
...
├── raw_observables.csv
...
```
Nominal observable values measured without decoding or post-selection, constructed from the measurements and the circuit annotation in the stim and cirq circuits. Contains both X and Z data. This is the data that decoders interpret, hence the subscript `_raw` as opposed to `_corrected`.

```
...
├── detector_error_model_X(Z).dem
...
```
The detector error model used to decode the data with [Tesseract](https://github.com/quantumlib/tesseract-decoder) for the tomography X(Z) data.

```
...
├── decoder_properties.json
...
```
Metadata for the decoder properties when running with Tesseract, related to the search algorithm. 
```
...
├── measurements.csv
...
```
The actual measurement data collected from the device. The detection event data and observable flip data is derived from this data. Contains both X and Z axis data. 

```
...
├── detection_events.csv
...
```
Detection event data, describing which detectors flipped and did not flip in each QEC shot. The detection event data is used by the decoders to predict whether or not the logical observable was flipped. The bits in every shot should be interpreted as `0` meaning "detector was not flipped" and `1` meaning "detector was flipped". Contains both X and Z data. 
```
...
├── corrected_observables.csv
...
```
Nominal observable values measured with decoding and post-selection. Contains both X and Z data. 

## Additional resources <a name="additional-resources"></a>

[Stim](https://github.com/quantumlib/Stim) repository on GitHub and the [Getting Started Notebook](https://github.com/quantumlib/Stim/blob/main/doc/getting_started.ipynb).

[Chromobius](https://github.com/quantumlib/chromobius) repository on GitHub.

[Surface code and repetition code datasets](https://doi.org/10.5281/zenodo.11403594) released in "Optimization of decoder priors for accurate quantum error correction" [[3]](#3).

[Surface code and repetition code datasets](https://zenodo.org/records/6804040) released in "Suppressing quantum errors by scaling a surface code logical qubit" [[7]](#7).

[Surface code and repetition code datasets](https://zenodo.org/records/13273331) released in "Quantum error correction below the surface code threshold" [[8]](#8).

[Color code datasets](https://zenodo.org/records/14238944) released in "Scaling and logic in the color code on a superconducting quantum processor" [[9]](#9).

## References <a name="references"></a>


<a id="1">[1]</a>
C. Gidney *et al.*,
[New circuits and an open source decoder for the color code](https://arxiv.org/abs/2312.08813)
arXiv:2312.08813 (2023)

<a id="2">[2]</a>
C. Gidney *et al.*,
[A fault-tolerant honeycomb memory](https://quantum-journal.org/papers/q-2021-12-20-605/)
Quantum 5, 605 (2021)

<a id="3">[3]</a>
V. Sivak *et al.*,
[Optimization of decoder priors for accurate quantum error correction](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.133.150603)
Phys. Rev. Lett. 133, 150603 (2024)

<a id="4">[4]</a>
A. Landahl *et al.*,
[Fault-tolerant quantum computing with color codes](https://arxiv.org/pdf/1108.5738)
arXiv:1108.5738 (2011)

<a id="5">[5]</a>
H. Wang *et al.*,
[Fault-tolerant quantum computing with color codes](https://arxiv.org/abs/2311.16214)
2311.16214 (2023)

<a id="6">[6]</a>
J. Bausch *et al.*,
[Learning high-accuracy error decoding for quantum processors](https://www.nature.com/articles/s41586-024-08148-8)
Nature (2024)

<a id="7">[7]</a>
Google Quantum AI,
[Suppressing quantum errors by scaling a surface code logical qubit](https://www.nature.com/articles/s41586-022-05434-1)
Nature 614, 676–681 (2023)

<a id="8">[8]</a>
Google Quantum AI,
[Quantum error correction below the surface code threshold](https://www.nature.com/articles/s41586-024-08449-y)
Nature 638, 920–926 (2025)

<a id="9">[9]</a>
Google Quantum AI,
[Scaling and logic in the color code on a superconducting quantum processor](https://www.nature.com/articles/s41586-025-09061-4)
Nature 645, 614–619 (2025)
