from entities import Patient
from pony.orm import db_session
import pydf
import concurrent.futures
import multiprocessing
from pathlib import Path
from tempfile import NamedTemporaryFile
import subprocess

OUTPUT_PATH = "/home/jimmy/mdk"


def append_pdf(file_path, tmp, paths):
    real_paths = " ".join([str(p.resolve()) for p in paths])
    cmd = f"gs -dBATCH -dNOPAUSE -sPAPERSIZE=A4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {real_paths}"
    subprocess.check_output(cmd, shell=True)


def make_paths(fods):
    for fod in fods:
        yield fod.path

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
            patient.P_pnom + "_" + patient.P_pprenom + "-" + ddn + ".pdf",
        )
    )
    append_pdf(file_path, tmp, make_paths(patient.fods))
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
        executor.map(proc_lot, chunk(50, 8))


if __name__ == "__main__":

    generate_all()
