#!/usr/bin/env python3
"""
Script to extract only 'Combined Power' lines from a carbon log file.
"""
import os
import re
import argparse
from pathlib import Path

def extract_combined_power(input_file, output_file=None):
    """
    Extract lines containing 'Combined Power' from the input file and write to output file.
    Also calculates the sum of all power values and appends it to the end of the output file.
    
    Args:
        input_file (str): Path to the input log file
        output_file (str, optional): Path to the output file. If None, creates a file with '_power_only' suffix
    
    Returns:
        tuple: (output_file_path, total_power_sum)
    """
    if output_file is None:
        # Create default output filename by adding '_power_only' before the extension
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_power_only{input_path.suffix}")
    
    combined_power_pattern = re.compile(r'.*Combined Power \(CPU \+ GPU \+ ANE\): (\d+) mW')
    
    # Read input file and extract lines
    extracted_lines = []
    total_power = 0
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = combined_power_pattern.match(line)
                if match:
                    power_value = int(match.group(1))
                    total_power += power_value
                    extracted_lines.append(line.strip())
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None
    
    # Write extracted lines to output file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in extracted_lines:
                f.write(f"{line}\n")
            # Add the total sum at the end of the file
            f.write(f"\nTotal Combined Power: {total_power} mW")
    except Exception as e:
        print(f"Error writing to output file: {e}")
        return None
    
    return output_file, total_power

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract Combined Power lines from carbon log files')
    parser.add_argument('input_file', help='Path to the input log file')
    parser.add_argument('-o', '--output', help='Path to the output file (optional)')
    
    args = parser.parse_args()
    
    result = extract_combined_power(args.input_file, args.output)
    
    if result:
        output_path, total_power = result
        print(f"Combined Power data has been extracted to: {output_path}")
        line_count = sum(1 for _ in open(output_path, 'r')) - 2  # Subtract 2 for the empty line and total sum line
        print(f"Total extracted lines: {line_count}")
        print(f"Total combined power sum: {total_power} mW")
    else:
        print("Failed to extract data")

if __name__ == "__main__":
    main()
