import argparse
import subprocess


def index_genome(genome: str) -> None:
    subprocess.run(
        [
            "python",
            "index_genome.py",
            "--genome",
            genome,
        ]
    )


def process_reads(
    threads: int, input_dir: str, output_dir: str, ref: str, logs: str, q: int
) -> None:
    subprocess.run(
        [
            "python",
            "process_reads.py",
            "--threads",
            str(threads),
            "--input_dir",
            input_dir,
            "--output_dir",
            output_dir,
            "--ref",
            ref,
            "--logs",
            logs,
            "--q",
            str(q),
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Main script for indexing genome or processing reads"
    )

    subparsers = parser.add_subparsers(
        dest="action", required=True, help="Action to perform: index or process"
    )

    # Subparser for indexing genome
    index_parser = subparsers.add_parser("index", help="Index the genome")
    index_parser.add_argument(
        "--genome", required=True, type=str, help="Path to the reference genome file"
    )

    # Subparser for processing reads
    process_parser = subparsers.add_parser("process", help="Process reads")
    process_parser.add_argument(
        "--threads", type=int, default=8, help="Number of threads"
    )
    process_parser.add_argument(
        "--input_dir", type=str, required=True, help="Abs path to input folder"
    )
    process_parser.add_argument(
        "--output_dir", type=str, required=True, help="Abs path to output folder"
    )
    process_parser.add_argument(
        "--ref", type=str, required=True, help="Abs path to genome file"
    )
    process_parser.add_argument(
        "--logs", type=str, required=True, help="Abs path to logs folder"
    )
    process_parser.add_argument(
        "--q", type=int, default=20, help="Quality score for trim_galore"
    )

    args = parser.parse_args()

    if args.action == "index":
        index_genome(genome=args.genome)
    elif args.action == "process":
        process_reads(
            threads=args.threads,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            ref=args.ref,
            logs=args.logs,
            q=args.q,
        )

