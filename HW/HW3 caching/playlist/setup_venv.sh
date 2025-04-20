#!/bin/bash

# Set the name of the virtual environment directory
VENV_DIR=
REQUIREMENTS_FILE=

# Check if the virtual environment already exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."


  # Install dependencies from requirements.lock if it exists
  if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."

  else
    echo "Error: $REQUIREMENTS_FILE not found."
    exit 1
  fi
else

  echo "Virtual environment already exists. Activated."
fi
