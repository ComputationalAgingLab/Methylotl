import os
import re
import subprocess
import argparse
import sys
import shutil
from typing import List, Tuple, Optional


def get_file_extension(folder: str) -> Tuple[str, str]:
    """
    Determines the platform-specific output file extensions from files in the given folder.
    Args:
        folder (str): The directory to scan for files.
    Returns:
        Tuple[str, str]: A tuple containing two file extensions.
    Raises:
        ValueError: If no valid file extensions are found.
    """
    platform_output1 = None
    platform_output2 = None

    valid_extensions = (
        "_1.fastq", "_1.fastq.gz",
        "_1.fq.gz", "_1.fq",
        "_R1.fq.gz", "_R1.fq",
        "_R1.fastq.gz", "_R1.fastq",
        "_R1_001.fq.gz", "_R1_001.fq",
        "_R1_001.fastq.gz", "_R1_001.fastq"
    )

    for filename in os.listdir(folder):
        for extension in valid_extensions:
            if filename.endswith(extension):
                platform_output1 = extension
                platform_output2 = platform_output1.replace("1", "2", 1)

            if platform_output1 and platform_output2:
                break

    if platform_output1 and platform_output2:
        return platform_output1, platform_output2
    else:
        raise ValueError("Wrong file format")


def process_filename(filename: str, platform_output: str) -> Tuple[str, Optional[str]]:
    """
    Extracts the sample name and line from the given filename.
    Args:
        filename (str): The filename to process.
        platform_output (str): The platform-specific file extension.
    Returns:
        Tuple[str, Optional[str]]: A tuple containing the sample name and the line (if found).
    """
    sample_name = filename.replace(platform_output, "")
    match = re.search(r'(L00[1-4])', sample_name)

    if match:
        line = match.group(1)
        sample_name = sample_name.split(line)[0]
    else:
        line = None

    return sample_name, line


def process_oneline_files(files: List[str], platform_output1: str, platform_output2: str, logpath: str, input_dir: str,
                          output_dir: str, args) -> None:
    """
    Processes files that do not have corresponding lines.
    Args:
        files (List[str]): List of file names to process.
        platform_output1 (str): First file output pattern.
        platform_output2 (str): Second file output pattern.
        logpath (str): Path to the log file.
        input_dir (str): Directory containing input files.
        output_dir (str): Directory to store output files.
    """
    r1 = None
    r2 = None
    name = None

    for file in files:
        if file.endswith(platform_output1):
            name, line = process_filename(file, platform_output1)
            if line:
                r1 = f"{name}{line}{platform_output1}"
            else:
                r1 = f"{name}{platform_output1}"
        elif file.endswith(platform_output2):
            name, line = process_filename(file, platform_output2)
            if line:
                r2 = f"{name}{line}{platform_output2}"
            else:
                r2 = f"{name}{platform_output2}"

    # Perform quality control
    print("QC...")
    qc_dir = os.path.join(output_dir, "FastQC")
    os.makedirs(qc_dir, exist_ok=True)
    qc_command = [
        "fastqc",
        "-o", qc_dir,
        "-t", str(args.threads),
        os.path.join(input_dir, r1),
        os.path.join(input_dir, r2)
    ]
    if platform_output1.endswith(".gz"):
        qc_command.insert(1, "--noextract")

    with open(logpath, "w") as logfile:
        subprocess.run(qc_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Adapter trimming
    print("Adapter trimming...")
    trimgalore_dir = os.path.join(output_dir, "trim-galore")
    os.makedirs(trimgalore_dir, exist_ok=True)
    trim_command = [
        "trim_galore",
        "-q", str(args.q),
        "--fastqc",
        "-o", trimgalore_dir,
        "-j", str(args.threads),
        "--paired",
        "--gzip",
        os.path.join(input_dir, r1),
        os.path.join(input_dir, r2),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(trim_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Aligning
    print("Aligning...")
    aligning_dir = os.path.join(output_dir, "aligning")
    os.makedirs(aligning_dir, exist_ok=True)
    align_command = [
        "bsmapz",
        "-a", os.path.join(trimgalore_dir, f"{name}_1_val_1.fq.gz"),
        "-b", os.path.join(trimgalore_dir, f"{name}_2_val_2.fq.gz"),
        "-d", args.ref,
        "-o", os.path.join(aligning_dir, f"{name}.bam"),
        "-p", str(args.threads),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(align_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Fixing mates
    fixmate_command = [
        "samtools", "fixmate", "-m",
        os.path.join(aligning_dir, f"{name}.bam"),
        os.path.join(aligning_dir, f"{name}.fixmate.bam"),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(fixmate_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Sorting BAM files
    sort_command = [
        "samtools", "sort", "-@", str(args.threads),
        "-o", os.path.join(aligning_dir, f"{name}.sorted.bam"),
        os.path.join(aligning_dir, f"{name}.fixmate.bam"),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(sort_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Deduplicating BAM files
    print("Deduplicating...")
    deduplicate_command = [
        "samtools", "markdup",
        os.path.join(aligning_dir, f"{name}.sorted.bam"),
        os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam"),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(deduplicate_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Collect stats
    collect_stats_command = [
        "samtools", "flagstat", os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam")
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(collect_stats_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Methylation extraction
    print("Methylation extraction...")
    extraction_dir = os.path.join(output_dir, "methyl_extraction")
    os.makedirs(extraction_dir, exist_ok=True)
    extraction_command = [
        "MethylDackel", "extract", "--fraction", "--minDepth", "10",
        args.ref,
        os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam"),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(extraction_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)
    bedgraph_file = f"{name}.sorted.deduplicated_CpG.meth.bedGraph"
    extracted_bedgraph = os.path.join(aligning_dir, bedgraph_file)
    shutil.move(extracted_bedgraph, os.path.join(extraction_dir, bedgraph_file))

    # M-bias plotting
    mbias_command = [
        "MethylDackel", "mbias",
        args.ref,
        os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam"),
        f"{name}"
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(mbias_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)
    svg_files = [f"{name}_OB.svg", f"{name}_OT.svg"]
    for svg_file in svg_files:
        shutil.move(svg_file, os.path.join(extraction_dir, svg_file))


def process_multiline_files(files: List[str], platform_output1: str, platform_output2: str, logpath: str,
                            input_dir: str, output_dir: str, args) -> None:
    """
    Processes files where each file has a corresponding line value.

    Args:
        files (List[str]): List of file names to process.
        platform_output1 (str): First file output pattern.
        platform_output2 (str): Second file output pattern.
        logpath (str): Path to the log file.
        input_dir (str): Directory containing input files.
        output_dir (str): Directory to store output files.
    """
    name = None
    lines = []
    bams = []

    # Extract lines and names from files
    for file in files:
        if file.endswith(platform_output1):
            name, line = process_filename(file, platform_output1)
            lines.append(line)

    # Process each line
    for line in lines:
        r1 = f"{name}{line}{platform_output1}"
        r2 = f"{name}{line}{platform_output2}"

        # Perform quality control
        print("QC...")
        qc_dir = os.path.join(output_dir, "FastQC")
        os.makedirs(qc_dir, exist_ok=True)
        qc_command = [
            "fastqc",
            "-o", qc_dir,
            "-t", str(args.threads),
            os.path.join(input_dir, r1),
            os.path.join(input_dir, r2)
        ]
        if platform_output1.endswith(".gz"):
            qc_command.insert(1, "--noextract")

        with open(logpath, "w") as logfile:
            subprocess.run(qc_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

        # Adapter trimming
        print("Adapter trimming...")
        trimgalore_dir = os.path.join(output_dir, "trim-galore")
        os.makedirs(trimgalore_dir, exist_ok=True)
        trim_command = [
            "trim_galore",
            "-q", str(args.q),
            "--fastqc",
            "-o", trimgalore_dir,
            "-j", str(args.threads),
            "--paired",
            "--gzip",
            os.path.join(input_dir, r1),
            os.path.join(input_dir, r2),
        ]
        with open(logpath, "a") as logfile:
            subprocess.run(trim_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

        # Aligning
        print("Aligning...")
        aligning_dir = os.path.join(output_dir, "aligning")
        os.makedirs(aligning_dir, exist_ok=True)
        align_command = [
            "bsmapz",
            "-a", os.path.join(trimgalore_dir, f"{name}{line}_1_val_1.fq.gz"),
            "-b", os.path.join(trimgalore_dir, f"{name}{line}_2_val_2.fq.gz"),
            "-d", args.ref,
            "-o", os.path.join(aligning_dir, f"{name}{line}.bam"),
            "-p", str(args.threads),
        ]
        with open(logpath, "a") as logfile:
            subprocess.run(align_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

        # Fixing mates
        fixmate_command = [
            "samtools", "fixmate", "-m",
            os.path.join(aligning_dir, f"{name}{line}.bam"),
            os.path.join(aligning_dir, f"{name}{line}.fixmate.bam"),
        ]
        with open(logpath, "a") as logfile:
            subprocess.run(fixmate_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

        # Sorting BAM files
        sort_command = [
            "samtools", "sort", "-@", str(args.threads),
            "-o", os.path.join(aligning_dir, f"{name}{line}.sorted.bam"),
            os.path.join(aligning_dir, f"{name}{line}.fixmate.bam"),
        ]
        with open(logpath, "a") as logfile:
            subprocess.run(sort_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

        # Deduplicating BAM files
        print("Deduplicating...")
        deduplicate_command = [
            "samtools", "markdup",
            os.path.join(aligning_dir, f"{name}{line}.sorted.bam"),
            os.path.join(aligning_dir, f"{name}{line}.sorted.deduplicated.bam"),
        ]
        with open(logpath, "a") as logfile:
            subprocess.run(deduplicate_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

        # Collect BAM files for merging
        bams.append(os.path.join(aligning_dir, f"{name}{line}.sorted.deduplicated.bam"))

    # Merging BAM files
    merge_bams_command = [
        "samtools", "merge", "-@", str(args.threads),
        os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam"), *bams
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(merge_bams_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    #Collect stats
    collect_stats_command = [
        "samtools", "flagstat", os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam")
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(collect_stats_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)

    # Methylation extraction
    print("Methylation extraction...")
    extraction_dir = os.path.join(output_dir, "methyl_extraction")
    os.makedirs(extraction_dir, exist_ok=True)
    extraction_command = [
        "MethylDackel", "extract", "--fraction", "--minDepth", "10",
        args.ref,
        os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam"),
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(extraction_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)
    bedgraph_file = f"{name}.sorted.deduplicated_CpG.meth.bedGraph"
    extracted_bedgraph = os.path.join(aligning_dir, bedgraph_file)
    shutil.move(extracted_bedgraph, os.path.join(extraction_dir, bedgraph_file))

    # M-bias plotting
    mbias_command = [
        "MethylDackel", "mbias",
        args.ref,
        os.path.join(aligning_dir, f"{name}.sorted.deduplicated.bam"),
        f"{name}"
    ]
    with open(logpath, "a") as logfile:
        subprocess.run(mbias_command, stdout=logfile, stderr=subprocess.STDOUT, text=True)
    svg_files = [f"{name}_OB.svg", f"{name}_OT.svg"]
    for svg_file in svg_files:
        shutil.move(svg_file, os.path.join(extraction_dir, svg_file))


def main(args):
    print("CPU count:", args.threads)

    input_dir = args.input_dir

    log_dir = args.logs
    os.makedirs(log_dir, exist_ok=True)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    if not os.listdir(input_dir):
        print("Empty input directory")
        sys.exit(1)
    else:
        files_grouped = {}
        platform_output1, platform_output2 = get_file_extension(input_dir)
        for infile in os.listdir(input_dir):
            if infile.endswith(platform_output1):
                name, line = process_filename(infile, platform_output1)
                if name not in files_grouped:
                    files_grouped[name] = []
                files_grouped[name].append(infile)
            elif infile.endswith(platform_output2):
                name, line = process_filename(infile, platform_output2)
                if name not in files_grouped:
                    files_grouped[name] = []
                files_grouped[name].append(infile)

        for name, files in files_grouped.items():
            logpath = os.path.join(log_dir, f"{name}.log")
            if len(files) == 2:
                process_oneline_files(files, platform_output1, platform_output2, logpath, input_dir, output_dir, args)
            elif len(files) > 2:
                if len(files) % 2 == 0:
                    process_multiline_files(files, platform_output1, platform_output2, logpath, input_dir,
                                           output_dir, args)
            else:
                raise ValueError(f"Number of files for '{name}' does not match paired reads")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run pipeline")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads")
    parser.add_argument("--input_dir", type=str, required=True, help="Abs path to input folder")
    parser.add_argument("--output_dir", type=str, required=True, help="Abs path to output folder")
    parser.add_argument("--ref", type=str, required=True, help="Abs path to genome filer")
    parser.add_argument("--logs", type=str, required=True, help="Abs path to logs folder")
    parser.add_argument("--q", type=int, default=20, help="Quality score for trim_galore")
    args = parser.parse_args()

    main(args)

