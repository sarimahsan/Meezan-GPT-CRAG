import os
import json

folder_path = "../ScrappedData"  

total_words = 0
file_count = 0
skipped = 0

for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

                # Extract word_count safely
                word_count = data.get("metadata", {}).get("word_count")

                if word_count is not None:
                    total_words += word_count
                    file_count += 1
                else:
                    skipped += 1

        except Exception as e:
            print(f"[!] Error reading {filename}: {e}")
            skipped += 1

print("=" * 40)
print(f"📄 Files processed : {file_count}")
print(f"❌ Skipped files   : {skipped}")
print(f"🧠 Total words     : {total_words}")
print("=" * 40)