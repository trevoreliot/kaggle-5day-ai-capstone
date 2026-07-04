import json

with open("kaggle_notebook.ipynb", "r") as f:
    nb = json.load(f)

# Fix Cell 2 (mcp.list_tools)
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])
        if "mcp.list_tools()" in source:
            new_source = source.replace("mcp.list_tools()", "await mcp.list_tools()")
            cell["source"] = [line + ("\n" if not line.endswith("\n") else "") for line in new_source.splitlines()]

# Fix Cell 5 (genai.Client)
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = "".join(cell["source"])
        if "client = genai.Client()" in source:
            new_source = source.replace("client = genai.Client()", "try:\n    client = genai.Client()\n    print('Gemini Client Initialized! Prompts loaded successfully.')\nexcept Exception as e:\n    print(f'Skipping Gemini initialization: {e}')")
            new_source = new_source.replace("print(\"Gemini Client Initialized! Prompts loaded successfully.\")", "")
            cell["source"] = [line + ("\n" if not line.endswith("\n") else "") for line in new_source.splitlines()]

with open("kaggle_notebook.ipynb", "w") as f:
    json.dump(nb, f, indent=1)
