from PyPDF2 import PdfFileMerger, PdfFileReader
from entities import Patient
from pony.orm import db_session
import pydf


class FodMerge:
    def __init__(self, patient):
        self.filename = '_'.join((nom, prenom, ddn.strftime('%d-%m-%Y')))+".pdf"

    # def dispatch():


def merge(paths): 
    merger = PdfFileMerger()
    for file in paths:
        merger.append(PdfFileReader(open(file, 'rb')))
    merger.write("output.pdf")


@db_session
def gen_py():
    texte = Patient[1367].content()
    pdf = pydf.generate_pdf(texte)
    with open('test_doc.pdf', 'wb') as f:
        f.write(pdf)

if __name__ == '__main__':
    # p = Path('../fixtures')
    # files = [p / ".".join((str(n), 'pdf')) for n in range(1,4)]
    # merge(files)
    gen_py()