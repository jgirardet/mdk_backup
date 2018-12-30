from entities import Patient
from pony.orm import db_session, select
import pydf
from concurrent import futures
import multiprocessing
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import subprocess
import shutil

OUTPUT_PATH = "/home/jimmy/mdk"
TO_CONVERT = {".doc", ".docx", ".etf", ".o", ".rtf", ".xls"}

merge_pdf_failed = multiprocessing.Queue()

TMPDIR = TemporaryDirectory()


def clean_formats(fods):
    paths = []

    for fod in fods:
        if fod.path.suffix in TO_CONVERT:
            conv = subprocess.run(
                f"soffice --headless --convert-to pdf {str(fod.path)} --outdir {TMPDIR.name}",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
            )
            try:
                conv.check_returncode()
            except subprocess.CalledProcessError as err:
                print(err)
            else:
                paths.append(str(Path(TMPDIR.name, fod.path.stem + ".pdf")))
        elif fod.path.suffix == ".o":
            continue
        else:
            paths.append(str(fod.path))

    return " ".join(paths)


def append_pdf(file_path, tmp, patient):

    fods_path = clean_formats(patient.used_fods)

    if not fods_path:
        shutil.copy(tmp, file_path)
        return

    cmd = f"gs -q -dBATCH -dNOPAUSE -sPAPERSIZE=a4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {fods_path}"
    res = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    try:
        res.check_returncode()
    except subprocess.CalledProcessError as err:
        merge_pdf_failed.put(str(patient.patient_id) + " " + str(patient) + " ")
        print(err.stdout.decode())


@db_session
def process_one(patient: Patient):
    """crée un pdf depuis le contenu de la base"""

    if not isinstance(patient, Patient):
        patient = Patient[patient]
    # print(patient)
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

    # print(f"range: {range} terminée")


def chunk(total, size):
    index = 0
    while index != total:
        if index + size < total:
            yield (index, index + size)
            index += size
        else:
            yield (index, total)
            index = total


# @db_session
def generate_all():
    with db_session:
        # total = Patient.select().count()
        # total = Patient.select(lambda)[:100]
        total = select(p.patient_id for p in Patient)[:]#[:1000]

    # with futures.ProcessPoolExecutor(
    #     max_workers=multiprocessing.cpu_count() * 2
    # ) as executor:
    #     executor.map(proc_lot, chunk(1000, 8))

    with futures.ProcessPoolExecutor(
        max_workers=multiprocessing.cpu_count() * 2
    ) as executor:

        tasks = {}
        for patient_id in total:
            tasks[executor.submit(process_one, patient_id)] = patient_id

        # for task in futures.as_completed(tasks):
        #     print(task.result())
        #     print(task.exception())


if __name__ == "__main__":

    generate_all()

    # {'.doc', '.docx', '.etf', '.o', '.pdf', '.rtf', '.xls'}

    #1851 D'HAILLECOURT Raymond  14011 M'HAMED Benamrane  15721 PEOC'H Elea 
    # séparé en répertoire par nom

    # process_one(504)
    while not merge_pdf_failed.empty():
        print(merge_pdf_failed.get())
