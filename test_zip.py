import zipfile
import shutil
import os
import tempfile
import time

with zipfile.ZipFile("mock_export.zip", "w") as zf:
    zf.write("tmp_invoices/Invoices.csv", "Invoices.csv")
    zf.write("tmp_invoices/Transactions.csv", "Transactions.csv")
    zf.write("tmp_invoices/Cards.csv", "Cards.csv")

os.makedirs(os.path.expanduser("~/Desktop/Chargebee_Invoices"), exist_ok=True)
shutil.copy("mock_export.zip", os.path.expanduser("~/Desktop/Chargebee_Invoices/mock_export.zip"))
print("Dropped mock_export.zip into Magic Folder")
