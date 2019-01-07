from entities import Patient
from pony.orm import db_session, select
import pydf
from concurrent import futures
import multiprocessing
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
import subprocess
import shutil
import string
import os.path
import time
import datetime

OUTPUT_PATH = "/home/jimmy/mdk"
TO_CONVERT = {".doc", ".docx", ".etf", ".o", ".rtf", ".xls"}

merge_pdf_failed = multiprocessing.Queue()

TMPDIR = TemporaryDirectory()

LOG = multiprocessing.get_logger()
# LOG.setLevel(logging.INFO)

TEMP_SOFFICE = TemporaryDirectory()


def clean_formats(fods):
    paths = []

    LOG.info("fods : %s", fods)

    for fod in fods:
        if fod.path.suffix in TO_CONVERT:
            conv = subprocess.run(
                f"soffice --headless --convert-to pdf {str(fod.path)} --outdir {TMPDIR.name} -env:UserInstallation=file://{TEMP_SOFFICE.name}",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
            )
            LOG.info("conv stdout: %s", conv.stdout.decode())
            try:
                conv.check_returncode()
            except subprocess.CalledProcessError as err:
                LOG.error("convertiseur: %s", err)
            else:
                paths.append(str(Path(TMPDIR.name, fod.path.stem + ".pdf")))
                assert Path(
                    paths[-1]
                ).exists(), "le fichier temporaire n'a pas été créé"
        elif fod.path.suffix == ".o":
            continue
        else:
            paths.append(str(fod.path))
    LOG.info("after clean formats: %s", paths)
    return " ".join(paths)


def append_pdf(file_path, tmp, patient):

    LOG.info("File path: %s \n tmp: %s \n patient: %s ", file_path, tmp, patient)

    fods_path = clean_formats(patient.used_fods)

    if not fods_path:
        shutil.copy(tmp, file_path)
        return

    cmd = f"gs -q -dBATCH -dNOPAUSE -sPAPERSIZE=a4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {fods_path}"
    res = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )

    try:
        res.check_returncode()
    except subprocess.CalledProcessError as err:
        merge_pdf_failed.put(str(patient.patient_id) + " " + str(patient) + " ")
        LOG.error("error in append pdf:  %s", err.stdout.decode())


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

    output_path = os.path.join(OUTPUT_PATH, patient.P_pnom.lower()[0])

    file_path = os.path.join(
        output_path,
        # str(patient.patient_id)
        # + "~"
        patient.P_pnom.replace(" ", "_").replace("'", "-")
        + "~"
        + patient.P_pprenom.replace(" ", "_")
        + "~"
        + ddn
        + ".pdf",
        # patient.P_pnom.replace(' ','_') + "~" + patient.P_pprenom.replace(' ', '_') + "~" + ddn + ".pdf",
    )
    append_pdf(file_path, tmp, patient)
    tmp.unlink()
    return f"ok {patient.patient_id}"


def generate_all(start, end):

    debut = time.time()

    # count entries
    with db_session:
        total = select(p.patient_id for p in Patient)[start:end]  # [:1000]
        LOG.info("Total : %s", total)

    # run all in executor
    with futures.ProcessPoolExecutor(
        max_workers=multiprocessing.cpu_count() * 2
    ) as executor:

        tasks = {}

        for patient_id in total:
            tasks[executor.submit(process_one, patient_id)] = patient_id

        counter = 0
        for tk in futures.as_completed(tasks):
            counter += 1
            td = str(datetime.timedelta(seconds=time.time() - debut)).split(":")
            td[2] = td[2].split(".")[0]
            td = "Temps écoulé: {0}h {1}m {2}s".format(*td)
            # print(tk, end='\r', flush=True)
            print(
                "{0}/{1} : {2:0.0f}%     temps écoulé: {3}".format(
                    counter, len(total), counter / len(total) * 100, td
                ),
                end="\r"
            )


def create_arbo():

    for letter in string.ascii_lowercase:
        Path(OUTPUT_PATH, letter).mkdir(exist_ok=True)


if __name__ == "__main__":

    multiprocessing.log_to_stderr()

    create_arbo()

    generate_all(0, 14)

    # séparé en répertoire par nom

    # process_one(4)
    while not merge_pdf_failed.empty():
        print(merge_pdf_failed.get())
