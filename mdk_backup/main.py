from PyPDF2 import PdfFileMerger, PdfFileReader
import os
from pathlib import Path

class FodMerge:
    def __init__(self, patient):
        self.filename = '_'.join((nom, prenom, ddn.strftime('%d-%m-%Y')))+".pdf"

    # def dispatch():


def merge(paths): 
    merger = PdfFileMerger()
    for file in paths:
        merger.append(PdfFileReader(open(file, 'rb')))
    merger.write("output.pdf")


    # def write_pdf(merger):



if __name__ == '__main__':
    p = Path('../fixtures')
    files = [p / ".".join((str(n), 'pdf')) for n in range(1,4)]
    merge(files)