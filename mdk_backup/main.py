from entities import Patient
from pony.orm import db_session
import pydf
import concurrent.futures
import multiprocessing
from pathlib import Path
from tempfile import NamedTemporaryFile
import subprocess
import shutil

OUTPUT_PATH = "/home/jimmy/mdk"

merge_pdf_failed = multiprocessing.Queue()


def append_pdf(file_path, tmp, patient):
    fods = patient.used_fods
    if not fods:
        shutil.copy(tmp, file_path)
        return
    cmd = f"gs -q -dBATCH -dNOPAUSE -sPAPERSIZE=a4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {fods}"
    # subprocess.check_output(cmd, shell=True)
    res = subprocess.Popen(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True).wait()
    if res:
        merge_pdf_failed.put(str(patient.patient_id) + " " + str(patient))


def make_paths(fods):
    for fod in fods:
        yield fod


def process_one(patient: Patient):
    """crée un pdf depuis le contenu de la base"""
    texte = patient.content()
    pdf = pydf.generate_pdf(texte)
    ddn = patient.P_pddn.strftime("%d_%m_%Y") if patient.P_pddn else ""

    with NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as p:
        p.write(pdf)
        tmp = Path(p.name)

    file_path = "".join(
        (
            OUTPUT_PATH + "/",
            str(patient.patient_id)
            + "~"
            + patient.P_pnom.replace(" ", "_")
            + "~"
            + patient.P_pprenom.replace(" ", "_")
            + "~"
            + ddn
            + ".pdf",
            # patient.P_pnom.replace(' ','_') + "~" + patient.P_pprenom.replace(' ', '_') + "~" + ddn + ".pdf",
        )
    )
    append_pdf(file_path, tmp, patient)
    tmp.unlink()
    return f"ok {patient.patient_id}"


@db_session
def proc_lot(range):
    """wrapper necessaire pour db_session"""
    for p in Patient.select()[range[0] : range[1]]:
        process_one(p)

    print(f"range: {range} terminée")


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
        executor.map(proc_lot, chunk(100, 8))


if __name__ == "__main__":

    generate_all()
    while not merge_pdf_failed.empty():
        print(merge_pdf_failed.get())
