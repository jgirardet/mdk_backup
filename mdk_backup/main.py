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


import asyncio
async def append_pdf3(file_path, tmp, paths):
    real_paths = " ".join([str(p.resolve()) for p in paths])
    print(real_paths)
    cmd = f"gs -dBATCH -dNOPAUSE -sPAPERSIZE=A4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {real_paths}"
    cmd = cmd.split()
    print( cmd)
    p = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await p.wait()

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


async def process_deux(patient: Patient):
    """crée un pdf depuis le contenu de la base"""
    print('deuuuuuuuuux')
    # texte = patient.content()
    # pdf = pydf.generate_pdf(texte)
    apydf = pydf.AsyncPydf()
    pdf = await apydf.generate_pdf(patient.content())
    ddn = patient.P_pddn.strftime("%d_%m_%Y") if patient.P_pddn else ""

    

    with NamedTemporaryFile(delete=False,suffix=".pdf", mode="wb") as p:
        p.write(pdf)
        tmp = Path(p.name)

    file_path = "".join((OUTPUT_PATH+"/", patient.P_pnom + "_" + patient.P_pprenom + "-" + ddn + ".pdf"))
    await append_pdf3( file_path, tmp, make_paths(patient.fods))
    tmp.unlink()
    return f"ok {patient.patient_id}"



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
    # for p in Patient.select()[range[0] : range[1]]:

async def proc_trans(ranged):
    print("mkmok")
    tasks = [process_deux(p) for p in Patient.select()[ranged[0] : ranged[1]]]
    await asyncio.gather(*tasks)


@db_session
def proc_lot2(ranged):
    """wrapper necessaire pour db_session"""
    # for p in Patient.select()[range[0] : range[1]]:
    #     process_one(p)
    print("iljlijli")
    # tasks = [asyncio.create_task(process_deux(p)) for p in Patient.select()[ranged[0] : ranged[1]]]
    # asyncio.run(process_deux(Patient[45]))
    # loop = asyncio.get_running_loop()
    # loop.run_until_complete(tasks)
    # asyncio.run(*tasks)
    # asyncio.gather(*tasks)
    # asyncio.run(asyncio.gather(*tasks))
    print('iiiiiiiii')
    asyncio.run(proc_trans(ranged))
    # asyncio.run(asyncio.sleep(1))




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


def generate_all2():
    with db_session:
        total = Patient.select().count()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=multiprocessing.cpu_count() * 2
    ) as executor:
        executor.map(proc_lot2, chunk(50, 8))


if __name__ == "__main__":

    # generate_all()
    generate_all2()
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
