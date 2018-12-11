from PyPDF2 import PdfFileMerger, PdfFileReader
from entities import Patient
from pony.orm import db_session
import pydf
import concurrent.futures
import multiprocessing
from pathlib import Path
from  tempfile import NamedTemporaryFile

OUTPUT_PATH = "/home/jimmy/mdk"
# MDK_FILES = 


def append_pdf(file_path, paths):
    merger = PdfFileMerger()
    # merger.append(PdfFileReader(file_path.resolve().open("rb")))
    # print(PdfFileReader("/home/jimmy/mdk/DEMO_Jeannine-28_03_1933.pdf"))
    # merger.append(PdfFileReader("/home/jimmy/mdk/DEMO_Jeannine-28_03_1933.pdf"))
    print(file_path)
    merger.append(PdfFileReader(str(file_path.resolve())))
    for file in paths:
        print(1)
        print(file.resolve())
        merger.append(PdfFileReader(str(file.resolve())))
    merger.write(str(file_path))

def append_pdf2(file_path, tmp, paths):
    real_paths = " ".join([str(p.resolve()) for p in paths])
    print(real_paths)
    cmd = f"gs -dBATCH -dNOPAUSE -sPAPERSIZE=A4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {real_paths}"
    print( cmd)
    import subprocess
    subprocess.check_output(cmd, shell=True)


def make_paths(fods):
    p = Path("../fixtures")
    for n in range(1, 4):
        yield p / ".".join((str(n), "pdf"))


def process_one(patient: Patient):
    """crée un pdf depuis le contenu de la base"""
    texte = patient.content()
    pdf = pydf.generate_pdf(texte)
    ddn = patient.P_pddn.strftime("%d_%m_%Y") if patient.P_pddn else ""

    

    with NamedTemporaryFile(delete=False,suffix=".pdf", mode="wb") as p:
        p.write(pdf)
        tmp = Path(p.name)

    file_path = "".join((OUTPUT_PATH+"/", patient.P_pnom + "_" + patient.P_pprenom + "-" + ddn + ".pdf"))
    append_pdf2( file_path, tmp, make_paths(patient.fods))
    tmp.unlink()
    return f"ok {patient.patient_id}"

@db_session
def proc_lot(range):
    """wrapper necessaire pour db_session"""
    for p in Patient.select()[range[0] : range[1]]:
        process_one(p)


def chunk(total, size):
    index = 0
    while index != total:
        if index + size < total:
            yield (index, index + size)
            index += size
        else:
            yield (index, total)
            index = total


def generate_all():
    with db_session:
        total = Patient.select().count()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=multiprocessing.cpu_count() * 2
    ) as executor:
        executor.map(proc_lot, chunk(1, 8))


if __name__ == "__main__":

    generate_all()
    # p = Path('../fixtures')
    # files = [p / ".".join((str(n), 'pdf')) for n in range(1,4)]
    # merge(files)
    # import time

    # MdkBackup().generate_pdf_from_texte_async()
    # MdkBackup().generate_pdf_from_texte()
    # @db_session
    # def rien():
    #     MdkBackup().process_one(Patient[481])
    # # rien()
    # pp =[]
    # item = 0
    # for i in range():
    #     p = MdkProcess(item,100)
    #     p.start()
    #     item +=100
    # pp.append(p)

    # for i, z in enumerate(pp):
    #     z.run()
