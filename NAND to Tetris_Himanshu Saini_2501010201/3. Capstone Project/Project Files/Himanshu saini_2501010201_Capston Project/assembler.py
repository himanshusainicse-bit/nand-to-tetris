"""
Hack Assembler - Nand to Tetris Capstone Project
Student K = 1  =>  K mod 3 = 1
Extra feature: For a wrong/invalid line, print a clear error message with
               the line number (e.g. "Line 7: invalid instruction")
               instead of crashing.

Usage:
    python assembler.py <input.asm>
Output:
    <input.hack>  (same folder as input file)
"""

import sys
import os
from typing import Optional, Tuple, List

# ---------------------------------------------------------------------------
# Predefined symbols
# ---------------------------------------------------------------------------
PREDEFINED = {
    'SP':     0,  'LCL':  1,  'ARG': 2,  'THIS': 3, 'THAT': 4,
    'R0':     0,  'R1':   1,  'R2':  2,  'R3':  3,
    'R4':     4,  'R5':   5,  'R6':  6,  'R7':  7,
    'R8':     8,  'R9':   9,  'R10': 10, 'R11': 11,
    'R12':   12,  'R13':  13, 'R14': 14, 'R15': 15,
    'SCREEN': 16384, 'KBD': 24576,
}

# ---------------------------------------------------------------------------
# C-instruction decode tables
# ---------------------------------------------------------------------------
COMP_TABLE = {
    '0':   '0101010', '1':   '0111111', '-1':  '0111010',
    'D':   '0001100', 'A':   '0110000', '!D':  '0001101',
    '!A':  '0110001', '-D':  '0001111', '-A':  '0110011',
    'D+1': '0011111', 'A+1': '0110111', 'D-1': '0001110',
    'A-1': '0110010', 'D+A': '0000010', 'D-A': '0010011',
    'A-D': '0000111', 'D&A': '0000000', 'D|A': '0010101',
    'M':   '1110000', '!M':  '1110001', '-M':  '1110011',
    'M+1': '1110111', 'M-1': '1110010', 'D+M': '1000010',
    'D-M': '1010011', 'M-D': '1000111', 'D&M': '1000000',
    'D|M': '1010101',
}

DEST_TABLE = {
    None:  '000', 'M':   '001', 'D':   '010', 'MD':  '011',
    'A':   '100', 'AM':  '101', 'AD':  '110', 'AMD': '111',
}

JUMP_TABLE = {
    None:  '000', 'JGT': '001', 'JEQ': '010', 'JGE': '011',
    'JLT': '100', 'JNE': '101', 'JLE': '110', 'JMP': '111',
}

# ---------------------------------------------------------------------------
# Helper: strip comments and whitespace from a raw line
# ---------------------------------------------------------------------------
def clean(line: str) -> str:
    idx = line.find('//')
    if idx != -1:
        line = line[:idx]
    return line.strip()

# ---------------------------------------------------------------------------
# Helper: encode A-instruction
# ---------------------------------------------------------------------------
def encode_a(value: int) -> str:
    return '0' + format(value, '015b')

# ---------------------------------------------------------------------------
# Helper: encode C-instruction  dest=comp;jump
# ---------------------------------------------------------------------------
def encode_c(line: str, line_no: int) -> Optional[str]:
    """
    Returns 16-bit binary string or None on error.
    On error, prints "Line <n>: invalid instruction" (K=1 extra feature).
    """
    dest_str = None
    jump_str = None
    comp_str = line

    # Split off jump
    if ';' in comp_str:
        parts = comp_str.split(';', 1)
        comp_str = parts[0].strip()
        jump_str = parts[1].strip()

    # Split off dest
    if '=' in comp_str:
        parts = comp_str.split('=', 1)
        dest_str = parts[0].strip()
        comp_str = parts[1].strip()

    # Validate
    if comp_str not in COMP_TABLE:
        print(f"Line {line_no}: invalid instruction (unknown comp '{comp_str}')")
        return None

    if dest_str not in DEST_TABLE:
        print(f"Line {line_no}: invalid instruction (unknown dest '{dest_str}')")
        return None

    if jump_str not in JUMP_TABLE:
        print(f"Line {line_no}: invalid instruction (unknown jump '{jump_str}')")
        return None

    return '111' + COMP_TABLE[comp_str] + DEST_TABLE[dest_str] + JUMP_TABLE[jump_str]

# ---------------------------------------------------------------------------
# PASS 1 — build symbol table (labels only)
# ---------------------------------------------------------------------------
def pass1(lines: list[str]) -> dict:
    """
    Strips comments/blanks; records (LABEL) → ROM address.
    Returns symbol_table dict.
    """
    symbol_table = dict(PREDEFINED)
    rom_addr = 0

    for raw in lines:
        line = clean(raw)
        if not line:
            continue
        if line.startswith('(') and line.endswith(')'):
            label = line[1:-1]
            symbol_table[label] = rom_addr   # label points to NEXT instruction
        else:
            rom_addr += 1

    return symbol_table

# ---------------------------------------------------------------------------
# PASS 2 — translate instructions to binary
# ---------------------------------------------------------------------------
def pass2(lines: List[str], symbol_table: dict) -> Tuple[List[str], int]:
    """
    Translates every real instruction to 16-bit binary.
    New variables get RAM addresses starting at 16.
    Returns list of binary strings.
    K=1 extra feature: prints error with original line number instead of crashing.
    """
    binary_lines = []
    next_var_addr = 16
    errors = 0

    # We track the ORIGINAL file line number for error messages.
    for file_line_no, raw in enumerate(lines, start=1):
        line = clean(raw)
        if not line:
            continue
        if line.startswith('(') and line.endswith(')'):
            continue  # label declaration — skip

        # --- A-instruction ---
        if line.startswith('@'):
            symbol = line[1:]
            if symbol.isdigit():
                value = int(symbol)
            else:
                # Look up or allocate
                if symbol not in symbol_table:
                    symbol_table[symbol] = next_var_addr
                    next_var_addr += 1
                value = symbol_table[symbol]
            binary_lines.append(encode_a(value))

        # --- C-instruction ---
        else:
            result = encode_c(line, file_line_no)
            if result is None:
                errors += 1
                # K=1 extra feature: continue instead of crashing,
                # error message already printed inside encode_c
            else:
                binary_lines.append(result)

    return binary_lines, errors

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def assemble(input_path: str):
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r') as f:
        lines = f.readlines()

    print(f"Assembling: {input_path}")

    # Pass 1
    symbol_table = pass1(lines)

    # Pass 2
    binary_lines, errors = pass2(lines, symbol_table)

    if errors:
        print(f"\n{errors} error(s) found. Output may be incomplete.")

    # Write output
    base = os.path.splitext(input_path)[0]
    output_path = base + '.hack'

    with open(output_path, 'w') as f:
        for b in binary_lines:
            f.write(b + '\n')

    print(f"Output written to: {output_path}  ({len(binary_lines)} instructions)")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <file.asm>")
        sys.exit(1)
    assemble(sys.argv[1])
