import argparse
import subprocess
import os

def index_genome(genome_file: str) -> None:
    """
    Indexes the genome file using samtools faidx.
    Args:
        genome_file (str): Path to the genome file.
    Returns:
        None. Prints a message indicating the completion of indexing.
    Raises:
        FileNotFoundError: If the specified genome file is not found.
    """
    index_file = genome_file + ".fai"
    subprocess.run(["samtools", "faidx", genome_file])
    print(f"Genome indexed. Index file saved as: {index_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genome indexing script using samtools faidx")
    parser.add_argument("--genome", required=True, help="Path to the genome file")
    args = parser.parse_args()

    genome_file = args.genome

    if not os.path.isfile(genome_file):
        raise FileNotFoundError("Genome file not found.")
    else:
        index_genome(genome_file)
