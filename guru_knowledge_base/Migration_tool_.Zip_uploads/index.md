# Migration tool .Zip uploads

> **Collection:** Customer Success
> **Last Modified:** 2023-03-27
> **Tags:** Andreea, data migration, large files, migration, migration tool, zip files

---

The migration tool now supports uploading ZIP archives. They can contain multiple CSV files or just one archived large file.

There are a couple of caveats on importing ZIP files:

1. **ZIPs MUST:**
  1. Be ZIP archives (no other archive format is supported);
  1. Only contain CSV files;
  1. Have the CSV files in the root of the archive (no folders, sub-folders, nothing).

1. **CSVs MUST:**
  1. Have a valid CSV format;
  1. Have the header on the first row;
  1. Only contain text (as in not binary data);
  1. Be encoded in UTF-8 (no UTF-16 support);
  1. Have enclosures (cells are surrounded by enclosing characters - quotes are strongly recommended) if they have non-standard delimiters (eg.: Tabs, Semicolons, any-other-character-some-creative-n*tjob-thought-it-would-be-cool-to-use-as-a-delimiter).

1. Even though you can reduce huge CSV files to a few MB by archiving them, please take into account that the migration processes still need to go through their entire content and might crash for large amount of data, so **eliminate as much unnecessary data from them as you can**.

After uploading one of the files, wait for the validation to finish (there's no visual indicator, but it's happening behind the scenes). 

Continue with uploading the second file **only after/if you get the "validated" message for the first** (it can take up to 2-3min for large files).
