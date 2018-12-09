from PyPDF2 import PdfFileMerger, PdfFileReader
from entities import Patient
from pony.orm import db_session
import pydf


class FodMerge:
    def __init__(self, patient):
        self.filename = '_'.join((nom, prenom, ddn.strftime('%d-%m-%Y')))+".pdf"

    # def dispatch():



class MdkBackup:
    def __init__(self):
        pass

    @db_session
    def generate_pdf_from_texte(self):
        for patient in Patient.select():
            texte = patient.content()
            pdf = pydf.generate_pdf(texte)
            with open(f'{patient.P_pnom}_{patient.P_pprenom}_{patient.P_pddn}.pdf', 'wb') as f:
                f.write(pdf)
        

def merge_existing_pdf(paths): 
    merger = PdfFileMerger()
    for file in paths:
        merger.append(PdfFileReader(open(file, 'rb')))
    merger.write("/home/jimmy/mdk/output.pdf")



if __name__ == '__main__':
    # p = Path('../fixtures')
    # files = [p / ".".join((str(n), 'pdf')) for n in range(1,4)]
    # merge(files)
    import time
    
    MdkBackup().generate_pdf_from_texte()