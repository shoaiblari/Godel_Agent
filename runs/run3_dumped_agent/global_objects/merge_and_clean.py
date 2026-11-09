

def merge_and_clean(dump_folder='../dumped_agent'):
    """
    Merges Python files in specific subfolders, copies certain files to the root of the dump folder,
    and performs clean-up by removing folders after merging.
    """
    
    def merge_py_files(source_folder, exclude_files, output_file):
        """
        Merges Python files in a folder into one output file, excluding specified files.
        """
        py_files = [f for f in os.listdir(source_folder) if f.endswith('.py') and f not in exclude_files]
        merged_code = ""
        for py_file in py_files:
            with open(os.path.join(source_folder, py_file), 'r') as f:
                content = f.read()
                merged_code += f"# {py_file}\n" + content + "\n\n"
        with open(os.path.join(dump_folder, output_file), 'w') as f:
            f.write(merged_code)
        print(f"Merged {len(py_files)} files into {output_file}.")
    
    def copy_and_merge_imports(existing_file, merged_file):
        """
        Copies import lines from the existing file to the top of the merged file.
        """
        if not os.path.exists(existing_file):
            return
        
        # Read the existing imports from the original file
        with open(existing_file, 'r') as f:
            lines = f.readlines()
        imports = [line for line in lines if line.startswith("import ") or line.startswith("from ")]
        
        # Prepend the imports to the merged file
        with open(os.path.join(dump_folder, merged_file), 'r') as f:
            merged_code = f.read()
        
        with open(os.path.join(dump_folder, merged_file), 'w') as f:
            f.write("".join(imports) + "\n" + merged_code)
        print(f"Copied imports from {existing_file} to {merged_file}.")
    
    # Merge Python files in agent_module and task folders
    agent_module_folder = os.path.join(dump_folder, 'agent_module')
    task_folder = os.path.join(dump_folder, 'task')
    
    if os.path.exists(agent_module_folder):
        merge_py_files(agent_module_folder, exclude_files=[
            'ThreadPoolExecutor.py', 'Any.py', 'partial.py', 'as_completed.py', 'lru_cache.py', 'Game24Task.py', 'MathTask.py'
        ], output_file='agent_module.py')
    
    if os.path.exists(task_folder):
        merge_py_files(task_folder, exclude_files=[], output_file='task.py')
    
    # Copy key.env, goal_prompt.md, and main.py to the dump_folder
    for file_name in ['key.env', 'goal_prompt.md', 'main.py']:
        source_file = os.path.join(os.getcwd(), file_name)
        if os.path.exists(source_file):
            shutil.copy(source_file, dump_folder)
            print(f"Copied {file_name} to {dump_folder}.")
    
    # Copy imports from the original agent_module.py and task.py to the new merged files
    current_folder = os.getcwd()
    copy_and_merge_imports(os.path.join(current_folder, 'agent_module.py'), 'agent_module.py')
    copy_and_merge_imports(os.path.join(current_folder, 'task.py'), 'task.py')
    
    # Clean up: remove the agent_module and task folders
    if os.path.exists(agent_module_folder):
        shutil.rmtree(agent_module_folder)
        print(f"Removed folder {agent_module_folder}.")
    
    if os.path.exists(task_folder):
        shutil.rmtree(task_folder)
        print(f"Removed folder {task_folder}.")
    
    print(f"Merge and clean-up process completed.")
