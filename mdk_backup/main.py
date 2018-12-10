from PyPDF2 import PdfFileMerger, PdfFileReader
from entities import Patient
from pony.orm import db_session
import pydf
import concurrent.futures
import multiprocessing
from pathlib import Path

PATH = "/home/jimmy/mdk"


def append_pdf(file_path, paths):
    merger = PdfFileMerger()
    # merger.append(PdfFileReader(file_path.resolve().open("rb")))
    # print(PdfFileReader("/home/jimmy/mdk/DEMO_Jeannine-28_03_1933.pdf"))
    # merger.append(PdfFileReader("/home/jimmy/mdk/DEMO_Jeannine-28_03_1933.pdf"))
    import time
    time.sleep(2)
    merger.append(PdfFileReader(file_path.resolve().open("rb")))
    print(file_path)
    for file in paths:
        print(1)
        print(file.resolve())
        merger.append(PdfFileReader(file.resolve().open("rb")))
    merger.write(str(file_path))


def make_paths(fods):
    p = Path("../fixtures")
    for n in range(1, 4):
        yield p / ".".join((str(n), "pdf"))


def process_one(patient: Patient):
    """crée un pdf depuis le contenu de la base"""
    texte = patient.content()
    pdf = pydf.generate_pdf(texte)
    ddn = patient.P_pddn.strftime("%d_%m_%Y") if patient.P_pddn else ""

    file_path = Path(
        PATH, patient.P_pnom + "_" + patient.P_pprenom + "-" + ddn + ".pdf"
    )
    file_path.write_bytes(pdf)
    append_pdf( file_path, make_paths(patient.fods))
    return f"ok {patient.patient_id}"


def proc_lot(range):
    """wrapper necessaire pour db_session"""
    with db_session():
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
