from pony.orm import Database, Optional, db_session, PrimaryKey, Set, select
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
    antecedents = Set('Antecedent')
    allergies = Set('Allergie')
    certificats = Set('Certificat')
    courriers = Set('Courrier')

    def __repr__(self):
        return " ".join((self.P_pnom, self.P_pprenom))


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
    Cons_cmotifprincip = Optional(str)
    Cons_csympto = Optional(str)
    Cons_cexamen = Optional(str)
    Cons_causccard = Optional(str)
    Cons_cconclu = Optional(str)
    Cons_ckilos = Optional(int)
    Cons_ctaille = Optional(int)
    Cons_FK_P_pnum_id = Optional(Patient)
    lignes = Set("Ligne")


class Ligne(db.Entity):
    _table_ = "s_lignordo"
    ligne_ordo_id = PrimaryKey(int, column="Lo_id")
    Lo_duree = Optional(str)
    Lo_mat = Optional(Decimal)
    Lo_10h = Optional(Decimal)
    Lo_midi = Optional(Decimal)
    Lo_16h = Optional(Decimal)
    Lo_soir = Optional(Decimal)
    Lo_cou = Optional(Decimal)
    Lo_repas = Optional(str)
    Lo_FK_Cons_id = Optional(Consultation)
    Lo_FK_Vidal_id = Optional("Vidal")

    def __repr__(self):
        return repr(self.Lo_FK_Vidal_id)


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
    Ant_fam =  Optional(int)
    Ant_FK_P_pnum_id = Optional('Patient')

    def __repr__(self):
        return self.Ant_texte + ' ' + self.Ant_resume

class Allergie(db.Entity):
    _table_ = "s_f_allergies_pat"
    antecedent_id = PrimaryKey(int, column="Fap_id")
    Fap_Allergie_Nom = Optional(str)
    Fap_Allergie_Comment = Optional(str)
    Fap_P_pnum_id = Optional('Patient')

    def __repr__(self):
        return self.Fap_Allergie_Nom + ': ' + self.Fap_Allergie_Comment


class Certificat(db.Entity):
    _table_ = "s_certificat"
    certificat_id = PrimaryKey(int, column="Certif_id")
    Certif_date = Optional(date)
    Certif_titre = Optional(str)
    Certif_phrase = Optional(str)
    Certif_FK_P_pnum_id = Optional('Patient')

    def __repr__(self):
        return self.Certif_titre

class Courrier(db.Entity):
    _table_ = "s_courrier"
    courrier_id = PrimaryKey(int, column="C_id")
    C_date = Optional(date)
    C_adressage = Optional(str)
    C_entete = Optional(str)
    C_write = Optional(str)
    C_FK_P_pnum_id = Optional('Patient')


db.bind("mysql", host="localhost", user="j", passwd="j", db="basemdk", port=3306)
db.generate_mapping(create_tables=False)


@db_session
def patient():
    p = Patient[1367]
    print(p.to_dict(related_objects=True, with_collections=True))


@db_session
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


@db_session
def consultation():
    cons = select(a for a in Consultation if a.Cons_cdate > date(2018, 11, 25))
    print([a.to_dict(related_objects=True, with_collections=True) for a in cons])


@db_session
def ligne():
    lignes = select(a for a in Ligne if a.Lo_FK_Cons_id.Cons_cdate > date(2018, 11, 28))
    print([a.to_dict(related_objects=True) for a in lignes])


if __name__ == "__main__":
    patient()
    # fod()
    # consultation()
    # ligne()
