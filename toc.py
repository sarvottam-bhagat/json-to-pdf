import json
import os

with open("sample_data/test.json", "r", encoding="utf-8") as f:
    data = json.load(f)

toc = []
for section_id, section_data in data["gap_analysis_report"]["section_analyses"].items():
    section_title = section_data["section_title"]
    coverage_analysis = []
    for category, details in section_data["coverage_categories"].items():
        coverage_analysis.append(f"{category.replace('_', ' ').title()}: {details['checkpoint_count']} checkpoints")
    toc.append(f"Section {section_id}: {section_title}\n\t\t" + "\n\t\t".join(coverage_analysis))

os.makedirs("output", exist_ok=True)
with open("output/table_of_contents.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(toc))