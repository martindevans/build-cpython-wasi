import wasm_tools
import re
import sys
import os

def add_memory(input_path, output_path, initial_pages=1, max_pages=None, export_name="secondary_memory"):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    # 1. Read the WASM binary
    with open(input_path, "rb") as f:
        wasm_binary = f.read()

    # 2. Convert WASM to WAT (Text format)
    # wasm-tools automatically handles the multi-memory proposal support
    wat_text = wasm_tools.print(wasm_binary)

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

    # 4. Convert WAT back to WASM binary
    try:
        new_wasm_binary = wasm_tools.parse(modified_wat)
    except Exception as e:
        print("Error parsing modified WAT. Ensure the multi-memory proposal is supported.")
        print(e)
        sys.exit(1)

    # 5. Save the result
    with open(output_path, "wb") as f:
        f.write(new_wasm_binary)
    
    print(f"Success! Created {output_path} with an additional memory.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_memory.py <input.wasm> <output.wasm>")
    else:
        add_memory(sys.argv[1], sys.argv[2])