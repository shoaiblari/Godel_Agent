

def store_all_logic(dump_folder='../dumped_agent'):
    """
    Dumps all custom logic (functions, methods, classes) from memory into new files in a specified folder.
    Adds necessary imports and post-processes the files to make them runnable.
    """
    # Create the dump folder if it doesn't exist, or clean it up if it exists
    if os.path.exists(dump_folder):
        shutil.rmtree(dump_folder)  # Remove the old folder and create a fresh one
    os.makedirs(dump_folder)

    project_directory = os.getcwd()

    def get_imports(source_code):
        """
        Analyze the source code to extract any missing imports.
        This is a basic implementation. For more complex imports, you can analyze dependencies.
        """
        tree = ast.parse(source_code)
        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        import_lines = [ast.unparse(node) for node in imports]  # Get the actual import lines
        return "\n".join(import_lines) + "\n"

    def post_process(source_code):
        """
        Add missing imports or dependencies to make the dumped code runnable.
        """
        imports = get_imports(source_code)
        return f"{imports}\n{source_code}"

    def dump_object(obj, name, folder):
        try:
            source_code = get_source_code(obj, name)  # Assume get_custom_sources() retrieves the function/class source
            source_code = post_process(source_code)      # Post-process the code to add imports/dependencies
            file_name = f"{name}.py"
            file_path = os.path.join(folder, file_name)
            with open(file_path, 'w') as file:
                file.write(source_code)
            return f"Dumped {name} to {file_path}."
        except Exception as e:
            return f"Failed to dump {name}: {str(e)}"

    def process_module(module_name, module):
        if not hasattr(module, '__file__'):
            return []

        try:
            module_file_path = os.path.abspath(inspect.getfile(module))
        except Exception:
            return []

        if not module_file_path.startswith(project_directory):
            return []

        module_folder = os.path.join(dump_folder, module_name)
        os.makedirs(module_folder, exist_ok=True)

        tasks = []
        for name, obj in vars(module).items():
            if inspect.isfunction(obj) or inspect.isclass(obj):
                tasks.append((obj, name, module_folder))
        return tasks

    all_tasks = []
    for module_name, module in sys.modules.items():
        all_tasks.extend(process_module(module_name, module))

    # Process global objects
    global_folder = os.path.join(dump_folder, "global_objects")
    os.makedirs(global_folder, exist_ok=True)
    for name, obj in globals().items():
        if inspect.isfunction(obj) or inspect.isclass(obj):
            all_tasks.append((obj, name, global_folder))

    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(dump_object, *task) for task in all_tasks]
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    # merge_and_clean(dump_folder)
    print(f"All logic dumped into folder: {dump_folder}")
