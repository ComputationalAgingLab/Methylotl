<div style="float: right; margin-left: 20px;">   <img src="img/logo.jpg" alt="Methylotl" width="500"> </div>

# Methylotl



Methylotl is a Python package designed to process raw bisulfite sequencing data. It performs essential steps to convert, align, and analyze bisulfite-treated DNA sequences, providing insights into DNA methylation patterns.

## Features

- Aligns bisulfite-treated reads to a reference genome
- Analyzes methylation patterns

## Requirements

- Python 3.10 or higher

- Required Python packages: `pysam`

- External tools: `bsmapz`, `samtools`, `methyldackel`

**Note:** This script is designed to run on Linux distributions like Ubuntu 22.04. It may not work as expected on other operating systems.

## Installation

1. Clone the repository:

   ```{bash}
   git clone https://github.com/yourusername/Methylotl.git
   cd Methylotl
   ```

2.  Environment configurationvia conda or mamba:

   ```{bash}
   conda env create -n methylotl_env -f environment.yml
   conda activate methylotl_env
   ```

3. Ensure that `bsmapz` is installed and accessible in your PATH.

   ```{bash}
   export PATH=$PATH:/path/to/bsmapz
   ```

   

## Usage

### Basic Usage

To index the genome, run the following command:

```{bash}
python Methylotl.py index --genome /path/to/genome.fa
```
To process reads with default settings, use the following command:

```{bash}
python Methylotl.py process --input_dir /path/to/input --output_dir /path/to/output --ref /path/to/genome.fa --logs /path/to/logs --q 20
```

### Command-Line Arguments

- `index`: Index the genome.
- `process`: Process reads.
- `--genome`: Path to the reference genome file.
- `--threads`: Number of threads to use (default: 8).
- `--input_dir`: Absolute path to the input folder.
- `--output_dir`: Absolute path to the output folder.
- `--ref`: Absolute path to the genome file.
- `--logs`: Absolute path to the logs folder.
- `--q`: Quality score for trim_galore (default: 20).

## Output

Methylotl generates the following output files:

- FastQC reports: Before and after trimming
- Trimmed FASTQ files
- Unsorted BAM files
- Sorted BAM files
- Deduplicated BAM files
- BedGraph report
- Methylation bias (MBias) plot for each strand (in SVG format)
- Log files for each step of the process

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests with detailed descriptions of your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact

For questions or comments, please contact us ttnlsc@gmail.com , stacy.petukhova@gmail.com.
