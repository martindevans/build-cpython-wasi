import subprocess
import sys
import os
import re

# --- CONFIGURATION ---
# Path to your WABT binaries folder
WABT_BIN_PATH = "./../wabt/bin" 

def run_tool(tool_name, args, input_str=None):
    ext = ".exe" if os.name == 'nt' else ""
    tool_path = os.path.join(WABT_BIN_PATH, f"{tool_name}{ext}")
    
    if not os.path.exists(tool_path):
        print(f"Error: {tool_name} not found at {tool_path}")
        sys.exit(1)

    result = subprocess.run(
        [tool_path] + args,
        input=input_str,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running {tool_name}:")
        print(result.stderr)
        sys.exit(1)
        
    return result.stdout

def main():
    if len(sys.argv) < 4:
        print("Usage: python add_memory.py <input.wasm> <output.wasm> <memory_name>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    mem_name = sys.argv[3]

    # 1. Convert WASM to WAT (text format)
    # We use "-" for output to get the result in stdout
    print(f"Reading {input_file}...")
    wat_content = run_tool("wasm2wat", [input_file, "-o", "-"])

    # 2. Inject the memory declaration
    # We look for the start of the module '(module' and insert the memory after it.
    # (memory $name 1) creates a memory with 1 page (64KB)
    # (export "name" (memory $name)) makes it accessible to the host
    memory_def = f'\n  (memory ${mem_name} 1)\n  (export "{mem_name}" (memory ${mem_name}))'
    
    # Use regex to find the (module line and insert after it
    new_wat = re.sub(r'\(module', f'(module{memory_def}', wat_content, count=1)

    # 3. Convert WAT back to WASM
    # We use "-" for input to read from stdin
    # We add --enable-multi-memory in case there is already a memory defined
    print(f"Injecting memory '{mem_name}' and recompiling...")
    
    # Note: Using run_tool logic but for binary output, we need a slight tweak 
    # to handle the binary stream. We'll call wat2wasm directly here.
    ext = ".exe" if os.name == 'nt' else ""
    wat2wasm_path = os.path.join(WABT_BIN_PATH, f"wat2wasm{ext}")
    
    try:
        process = subprocess.Popen(
            [wat2wasm_path, "-", "--enable-multi-memory", "-o", output_file],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        _, stderr = process.communicate(input=new_wat)
        
        if process.returncode == 0:
            print(f"Successfully created: {output_file}")
        else:
            print("Error recompiling WASM:")
            print(stderr)
    except Exception as e:
        print(f"Failed to run wat2wasm: {e}")

if __name__ == "__main__":
    main()