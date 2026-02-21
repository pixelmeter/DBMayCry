import os
class FileHealthStorage:
    def __init__(self, filepath="health_logs.jsonl"):
        self.filepath = filepath
        # ensure file exists
        if not os.path.exists(filepath):
            open(filepath, "w").close()

    def save(self, report):
        with open(self.filepath, "a") as f:
            f.write(report.to_json() + "\n")