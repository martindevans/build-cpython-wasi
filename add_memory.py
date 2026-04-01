from wabt import Wabt
import re
import sys
import os
from pathlib import Path

def add_memory(input_path, output_path, initial_pages=1, max_pages=None, export_name="secondary_memory"):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    wabt = Wabt(skip_update=True)

    # 1. Read the WASM binary
    with open(input_path, "rb") as f:
        wasm_binary = f.read()

    # 2. Convert WASM to WAT (Text format)
    wabt.wasm_to_wat(input_path, output="temp.wat")
    wat_text = Path("temp.wat").read_text()

    # 3. Inject the new memory
    # We look for the first occurrence of '(memory' to place our new memory after it.
    # We also add an export so the host (JS/Python) can access it.
    max_str = f" {max_pages}" if max_pages else ""
    new_memory_def = f'\n  (memory (;1;) {initial_pages}{max_str})\n  (export "{export_name}" (memory 1))'
    
    # This regex finds the first memory definition and appends the second one after it
    # It handles both (memory 1) and (memory (;0;) 1) formats
    if "(memory" in wat_text:
        modified_wat = re.sub(r"(\(memory [^\)]+\))", r"\1" + new_memory_def, wat_text, count=1)
    else:
        # If the wasm somehow has no memory yet, we insert it at the start of the module
        modified_wat = re.sub(r"\(module", r"(module" + new_memory_def, wat_text)

    # Write back to WAT file
    Path("temp.wat").write_text(wat_text)

    # 4. Convert WAT back to WASM binary ans save result
    try:
        wabt.wat_to_wasm("temp.wat", output=output_path)
    except Exception as e:
        print("Error converting WAT to WASM.")
        print(e)
        sys.exit(1)
    
    print(f"Success! Created {output_path} with an additional memory.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_memory.py <input.wasm> <output.wasm>")
    else:
        add_memory(sys.argv[1], sys.argv[2])