from pony.orm import Database, Optional, db_session, PrimaryKey, Set, select, desc, UnrepeatableReadError
from datetime import datetime, date, timedelta
from decimal import Decimal

db = Database()


class Patient(db.Entity):
    _table_ = "s_patients"
    patient_id = PrimaryKey(int, column="P_pnum_id")
    P_pnom = Optional(str)
    P_pprenom = Optional(str)
    P_pddn = Optional(datetime)
    P_adr1 = Optional(str)
    P_adr2 = Optional(str)
    P_codp = Optional(str)
    P_ville = Optional(str)
    P_ptel = Optional(str)
    P_tel2 = Optional(str)
    P_tel3 = Optional(str)
    P_texte_libre = Optional(str)
    fods = Set("Fod")
    consultations = Set("Consultation")
    antecedents = Set("Antecedent")
    allergies = Set("Allergie")
    certificats = Set("Certificat")
    courriers = Set("Courrier")
    _examens = Set("Examen")
    bios = Set("Bio")

    @property
    def examens(self):
        return self._examens.select(lambda e: e.Ep_texte or e.Ep_resume)

    def __repr__(self):
        return " ".join((self.P_pnom, self.P_pprenom))

    def content(self):
        return f"""
{self.P_pnom} {self.P_pprenom} {self.P_pddn} {self.P_adr1} {self.P_adr2} {self.P_codp} {self.P_ville} {self.P_ptel} {self.P_tel2} {self.P_tel3}     
antécédents:  {" / ".join(a.content() for a in self.antecedents)}
allergies:  {" / ".join(a.content() for a in self.allergies)}

######################################################################

{"".join(c.content() for c in self.consultations.order_by(desc(Consultation.Cons_cdate)))}

######################################################################


{"".join(a.content() for a in self.certificats.order_by(desc(Certificat.Certif_date)))}

######################################################################

{"".join(a.content() for a in self.courriers.order_by(desc(Courrier.C_date)))}

######################################################################

{"".join(a.content() for a in self.examens.order_by(desc(Examen.Ep_dat)))}

######################################################################

{"".join(a.content() for a in self.bios.order_by(desc(Bio.X_ddate_resultats)))}

######################################################################

"""

class Fod(db.Entity):
    _table_ = "s_f_others_docs"
    fod_id = PrimaryKey(int, column="Fod_id")
    Fod_Fk = Optional(int)
    Fod_From = Optional(int)
    Fod_Name_Doc = Optional(str)
    Fod_Path_Doc = Optional(str)
    Fod_Type = Optional(int)
    Fod_FK_P_pnum_id = Optional(Patient)


class Consultation(db.Entity):
    _table_ = "s_consultations"
    consultation_id = PrimaryKey(int, column="Cons_id")

    Cons_cdate = Optional(date)
    Cons_ctascg = Optional(int)
    Cons_ctadcg = Optional(int)
    Cons_cfc = Optional(int)
    Cons_cmotifprincip = Optional(str)
    Cons_csympto = Optional(str)
    Cons_cexamen = Optional(str)
    Cons_causccard = Optional(str)
    Cons_cconclu = Optional(str)
    Cons_ckilos = Optional(int)
    Cons_ctaille = Optional(int)
    Cons_FK_P_pnum_id = Optional(Patient)
    lignes = Set("Ligne")

    def content(self):
        lignes = " | ".join([ligne.content() for ligne in self.lignes])
        return f"""{self.Cons_cdate}  {self.Cons_ctascg}/{self.Cons_ctadcg}mmHg {self.Cons_cfc}bpm {self.Cons_ctaille}m {self.Cons_ckilos}kg
{self.Cons_cmotifprincip}: {self.Cons_csympto}. {self.Cons_cexamen}. {self.Cons_causccard}. {self.Cons_cconclu}
{lignes}
--------------------------------------------------------
"""


class Ligne(db.Entity):
    _table_ = "s_lignordo"
    ligne_ordo_id = PrimaryKey(int, column="Lo_id")
    Lo_poso = Optional(str)
    Lo_autoposo = Optional(str)
    Lo_duree = Optional(str)
    Lo_FK_Cons_id = Optional(Consultation)
    Lo_FK_Vidal_id = Optional("Vidal")

    UNITE = {0: "boites", 1: "jours", 2: "semaines", 3: "mois", 4: "année"}

    @property
    def duree(self):
        try:
            nb, unite = self.Lo_duree.split("|")
        except ValueError:
            return ""
        return nb + " " + self.UNITE[int(unite)]

    def __repr__(self):
        return repr(
            str(self.ligne_ordo_id)
            + ": "
            + repr(self.Lo_FK_Vidal_id)
            + "->"
            + self.Lo_autoposo
            + " "
            + self.Lo_poso
            + " "
            + self.duree
        )

    def content(self):
        return (
            f"{self.Lo_FK_Vidal_id}"
        )  #: {self.Lo_autoposo} {self.Lo_poso} {self.duree}"


class Vidal(db.Entity):
    _table_ = "s_vidal"
    vidal_id = PrimaryKey(int, column="Vidal_id")

    Vidal_nommed = Optional(str)
    ligne = Set(Ligne)

    def __repr__(self):
        return self.Vidal_nommed


class Antecedent(db.Entity):
    _table_ = "s_antecedent"
    antecedent_id = PrimaryKey(int, column="Ant_id")
    Ant_date = Optional(date)
    Ant_texte = Optional(str)
    Ant_resume = Optional(str)
    Ant_fam = Optional(int)
    Ant_FK_P_pnum_id = Optional("Patient")

    def __repr__(self):
        return self.Ant_texte + " " + self.Ant_resume

    def content(self):
        return f"""{self.Ant_texte.strip()}: {self.Ant_resume.strip()} ({self.Ant_date.strftime('%Y') if self.Ant_date else ""}) {"fam" if self.Ant_fam else ""}"""

class Allergie(db.Entity):
    _table_ = "s_f_allergies_pat"
    antecedent_id = PrimaryKey(int, column="Fap_id")
    Fap_Allergie_Nom = Optional(str)
    Fap_Allergie_Comment = Optional(str)
    Fap_P_pnum_id = Optional("Patient")

    def __repr__(self):
        return self.Fap_Allergie_Nom + ": " + self.Fap_Allergie_Comment


    def content(self):
        return self.Fap_Allergie_Nom.strip() + ": " + self.Fap_Allergie_Comment.strip()


class Certificat(db.Entity):
    _table_ = "s_certificat"
    certificat_id = PrimaryKey(int, column="Certif_id")
    Certif_date = Optional(date)
    Certif_titre = Optional(str)
    Certif_phrase = Optional(str)
    Certif_FK_P_pnum_id = Optional("Patient")

    def __repr__(self):
        return self.Certif_titre

    def content(self):
        return f"""{self.Certif_date.strftime('%d %m %Y')} {self.Certif_titre.strip()}:{self.Certif_phrase.strip()}
--------------------------------------------------------
"""

class Courrier(db.Entity):
    _table_ = "s_courrier"
    courrier_id = PrimaryKey(int, column="C_id")
    C_date = Optional(date)
    C_adressage = Optional(str)
    C_entete = Optional(str)
    C_write = Optional(str)
    C_FK_P_pnum_id = Optional("Patient")


    def content(self):
        return f"""{self.C_date.strftime('%d %m %Y')} {self.C_entete} {self.C_adressage.strip()} {self.C_write.strip()}
--------------------------------------------------------
"""

class Examen(db.Entity):
    _table_ = "s_l_excomplementr"
    examen_id = PrimaryKey(int, column="Ep_id")
    Ep_dat = Optional(date)
    Ep_texte = Optional(str)
    Ep_resume = Optional(str)
    Ep_FK_P_pnum_id = Optional("Patient")
    Ep_FK_Ex_id = Optional('ExamenNom')

    def content(self):
        try:
            nom = self.Ep_FK_Ex_id.content()
        except UnrepeatableReadError:
            nom=""
        # date = self.Ep_dat.strftime('%d %m %Y') if  self.Ep_dat else ''
        return f"""{self.Ep_dat.strftime('%d %m %Y') if  self.Ep_dat else ''} {nom.strip()}  {self.Ep_texte.strip()} {self.Ep_resume.strip()}
--------------------------------------------------------
"""

class ExamenNom(db.Entity):
    _table_ ="s_ex_complementr"
    examen_nom_id = PrimaryKey(int, column="Ex_id")
    Ex_nom = Optional(str)
    examen = Set(Examen)

    def content(self):
        return f"{self.Ex_nom}"

class Bio(db.Entity):
    _table_ = "s_exam_demandes"
    bio_id = PrimaryKey(int, column="X_id")
    X_ddate_resultats = Optional(date)
    X_boite_olettre = Optional(str)
    X_FK_P_pnum_id = Optional("Patient")

    def content(self):
            return f"""{self.X_ddate_resultats.strftime('%d %m %Y') if self.X_ddate_resultats else ''} {self.X_boite_olettre.strip()}
-------------------------------------------------------- 
"""

db.bind("mysql", host="localhost", user="j", passwd="j", db="basemdk", port=3306)
db.generate_mapping(create_tables=False)


def patient(id):
    p = Patient[id]
    # print(p.to_dict(related_objects=True, with_collections=True))
    return p


def fod():
    fods = select(
        (
            a.Fod_From,
            a.Fod_Name_Doc,
            a.Fod_Path_Doc,
            a.Fod_Type,
            a.Fod_FK_P_pnum_id.P_pnom,
        )
        for a in Fod
    )
    print(list(fods[650:900]))


def consultation(id=None):
    if id:
        return Consultation[id].content()

    cons = select(a for a in Consultation if a.Cons_cdate > date(2018, 11, 25))
    print([a.to_dict(related_objects=True, with_collections=True) for a in cons])


def ligne(id=None):
    if id:
        return Ligne[id].to_dict(related_objects=True, with_collections=True)

    lignes = select(a for a in Ligne if a.Lo_FK_Cons_id.Cons_cdate > date(2018, 11, 28))
    print([a.to_dict(related_objects=True) for a in lignes])


@db_session
def main():
    # print(Patient[1367].content())
    print(Patient[490].content())
    with open('rien.txt', 'wt') as file:
        file.write(Patient[490].content())
    with open('rien2.txt', 'wt') as file:
        file.write(Patient[1367].content())
    # (list(print(f.to_dict()) for f in p.bios))
    # fod()
    # print(consultation(146280))
    # print(ligne(317741))
    # print(consultation(169672))
    # print(ligne(331011))
    # print(consultation(171004))
    # print(ligne(334408))
    # print(consultation(191750))
    # print(ligne(387539))
    # print(consultation(188947))
    # print(ligne(380639))


if __name__ == "__main__":
    main()
