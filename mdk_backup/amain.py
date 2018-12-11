from entities import Patient
from pony.orm import db_session
import pydf

import concurrent.futures
import multiprocessing
from pathlib import Path
from tempfile import NamedTemporaryFile
import asyncio

OUTPUT_PATH = "/home/jimmy/mdk"
# MDK_FILES =


def make_paths(fods):
    p = Path("../fixtures")
    for n in range(1, 4):
        yield p / ".".join((str(n), "pdf"))

async def run(cmd):
    proc = await asyncio.create_subprocess_exec(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    await proc.wait()

    # print(f'[{cmd!r} exited with {proc.returncode}]')
    # if stdout:
    #     print(f'[stdout]\n{stdout.decode()}')
    # if stderr:
    #     print(f'[stderr]\n{stderr.decode()}')


async def append_pdf2(file_path, tmp, paths):
    real_paths = " ".join([str(p.resolve()) for p in paths])
    print(real_paths)
    cmd = f"gs -dBATCH -dNOPAUSE -sPAPERSIZE=A4 -sDEVICE=pdfwrite -sOutputFile={file_path} {str(tmp)} {real_paths}"
    cmd = cmd.split()
    print( cmd)
    p = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await p.wait()

async def process_one(patient: Patient):
    """crée un pdf depuis le contenu de la base"""
    print("process one")
    apydf = pydf.AsyncPydf()
    pdf = await apydf.generate_pdf(patient.content())
    # pdf = pydf.generate_pdf(patient.content())


    with NamedTemporaryFile(delete=False,suffix=".pdf", mode="wb") as p:
        p.write(pdf)
        tmp = Path(p.name)

    
    ddn = patient.P_pddn.strftime("%d_%m_%Y") if patient.P_pddn else ""
    file_path = "".join((OUTPUT_PATH+"/", patient.P_pnom + "_" + patient.P_pprenom + "-" + ddn + ".pdf"))
    await append_pdf2( file_path, tmp, make_paths(patient.fods))
    tmp.unlink()
    # return f"ok {patient.patient_id}"



async def proc_lot(patients):
    """wrapper necessaire pour db_session"""
    tasks = [process_one(p) for p in patients]
    await asyncio.gather(*tasks)


def chunk(total, size):
    index = 0
    while index != total:
        if index + size < total:
            yield (index, index + size)
            index += size
        else:
            yield (index, total)
            index = total

@db_session
def generate_all():
    with db_session:
        total = Patient.select().count()

    tasks = [proc_lot(Patient.select()[d:f]) for d,f in chunk(50,8)]

    for task in tasks:
        asyncio.run(task)
    # await asyncio.gather(*tasks)



@db_session
def main():
    pass
if __name__ == "__main__":
    # main()
    generate_all()

    # generate_all3()
