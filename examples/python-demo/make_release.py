"""Create a tiny example artifact without third-party dependencies."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

output = Path(__file__).parent / "dist"
output.mkdir(exist_ok=True)
with ZipFile(output / "app.zip", "w", ZIP_DEFLATED) as archive:
    archive.writestr("app.py", 'print("Hello from ProjectSeal")\n')
print(output / "app.zip")
