#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define the environment file
ENV_FILE="environment.yml"

# Create the Conda environment from the YAML file
echo "Creating Conda environment from ${ENV_FILE}..."
conda env create -f $ENV_FILE

# Activate the newly created environment
echo "Activating the Conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate methylotl_env

# Clone the BSMAPz repository
echo "Cloning BSMAPz repository..."
git clone https://github.com/zyndagj/BSMAPz.git

# Navigate into the BSMAPz directory
cd BSMAPz

# Build BSMAPz
echo "Building BSMAPz..."
make bsmapz

# Add BSMAPz to the PATH within the environment
echo "Adding BSMAPz to PATH within the environment..."
export PATH=$PATH:$(pwd)

# Confirm installation
echo "BSMAPz installed successfully. Current PATH:"
echo $PATH

# Stay in the Conda environment
echo "Staying in the Conda environment: methylotl_env"
$SHELL

