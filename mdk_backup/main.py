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
import argparse
from loguru import logger

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
            LOG.info("conv stdout:")  # on laisse les 2 vu les probs d'ecnoding
            LOG.info(conv.stdout)

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

    texte = patient.content()
    pdf = pydf.generate_pdf(texte)
    ddn = patient.P_pddn.strftime("%d_%m_%Y") if patient.P_pddn else ""

    with NamedTemporaryFile(delete=False, suffix=".pdf", mode="wb") as p:
        p.write(pdf)
        tmp = Path(p.name)

    output_path = os.path.join(OUTPUT_PATH, patient.P_pnom.lower()[0])

    file_path = os.path.join(
        output_path,
        patient.P_pnom.replace(" ", "_").replace("'", "-")
        + "~"
        + patient.P_pprenom.replace(" ", "_")
        + "~"
        + ddn
        + ".pdf",
    )
    append_pdf(file_path, tmp, patient)
    tmp.unlink()
    return str(patient)


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
            end = "\r" if counter < len(total) else None
            print(
                "{0}/{1} : {2:0.0f}%     temps écoulé: {3}".format(
                    counter, len(total), counter / len(total) * 100, td
                ),
                end=end,
            )

def create_arbo():

    for letter in string.ascii_lowercase:
        Path(OUTPUT_PATH, letter).mkdir(exist_ok=True)


def main(debut, fin=None, one = False):

    create_arbo()
    if one:
        fin = debut +1
    generate_all(debut, fin)

    # séparé en répertoire par nom

    while not merge_pdf_failed.empty():
        print(merge_pdf_failed.get())


if __name__ == "__main__":
    import sys
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.info('info')
    logger.debug('debuga')
    logger.error('error')

    multiprocessing.log_to_stderr()

    parser = argparse.ArgumentParser(description="Utilitaire de sauvegarde médiclick")
    parser.add_argument(
        "debut",
        type=int,
        nargs="?",
        help="début d'intervalle ou dossier seul si fin absent, préciser 0 premier élément souhaité",
    )
    parser.add_argument(
        "fin", type=int, nargs="?", help="fin d'intervalle, default=infini"
    )
    parser.add_argument("--source", action="store", required=True, help = "Dossier source")
    parser.add_argument("--target", action="store", required=True, help = "Dossier cible")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Sauvegarde complète")

    group.add_argument("--solo", action="store_true", help="Sauvegarde d'un 1 seul dossier")

    args = parser.parse_args()


    if args.all:
        main(None, None)

    elif args.solo:
        if args.debut == None:
            parser.error("Un numéro de dossier doit être précisé")
        res = main(args.debut, one=True)

    elif args.debut and args.fin:
        main(args.debut, args.fin)

    else:
        parser.print_help()