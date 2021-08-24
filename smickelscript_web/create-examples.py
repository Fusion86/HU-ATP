import os
import json

examples = [["None", ""]]

for filename in os.listdir("../example_native"):
    filepath = os.path.join("../example_native", filename)

    with open(filepath, "r") as f:
        examples.append((filename, f.read()))

with open("public/examples.json", "w") as f:
    f.write(json.dumps(examples))
