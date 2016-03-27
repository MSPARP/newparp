import re

color_validator = re.compile("^[A-Fa-f0-9]{6}$")
username_validator = re.compile("^[-a-zA-Z0-9_]+$")
url_validator = re.compile("^[-a-zA-Z0-9_]+$")
email_validator = re.compile("^.+@.+\..+$")
secret_answer_replacer = re.compile("""[!?"'(),.\s]+""")

reserved_usernames = {
    "admin", "charat", "msparp", "official", "staff",
    "ectobiologist", "tentacletherapist", "turntechgodhead", "gardengnostic",
    "gutsygumshoe", "tipsygnostalgic", "timaeustestified", "golgothasterror",
    "apocalypsearisen", "adiostoreador", "twinarmageddons", "carcinogeneticist",
    "arseniccatnip", "grimauxiliatrix", "gallowscalibrator", "arachnidsgrip",
    "centaurstesticle", "terminallycapricious", "caligulasaquarium", "cuttlefishculler",
    "john_egbert", "rose_lalonde", "dave_strider", "jade_harley",
    "jane_crocker", "roxy_lalonde", "dirk_strider", "jake_english",
    "aradia_megido", "tavros_nitram", "sollux_captor", "karkat_vantas",
    "nepeta_leijon", "kanaya_maryam", "terezi_pyrope", "vriska_serket",
    "equius_zahhak", "gamzee_makara", "eridan_ampora", "feferi_peixes",
    "damara_megido", "rufioh_nitram", "mituna_captor", "kankri_vantas",
    "meulin_leijon", "porrim_maryam", "latula_pyrope", "aranea_serket",
    "horuss_zahhak", "kurloz_makara", "cronus_ampora", "meenah_peixes",
    "john-egbert", "rose-lalonde", "dave-strider", "jade-harley",
    "jane-crocker", "roxy-lalonde", "dirk-strider", "jake-english",
    "aradia-megido", "tavros-nitram", "sollux-captor", "karkat-vantas",
    "nepeta-leijon", "kanaya-maryam", "terezi-pyrope", "vriska-serket",
    "equius-zahhak", "gamzee-makara", "eridan-ampora", "feferi-peixes",
    "damara-megido", "rufioh-nitram", "mituna-captor", "kankri-vantas",
    "meulin-leijon", "porrim-maryam", "latula-pyrope", "aranea-serket",
    "horuss-zahhak", "kurloz-makara", "cronus-ampora", "meenah-peixes",
    "johnegbert", "roselalonde", "davestrider", "jadeharley",
    "janecrocker", "roxylalonde", "dirkstrider", "jakeenglish",
    "aradiamegido", "tavrosnitram", "solluxcaptor", "karkatvantas",
    "nepetaleijon", "kanayamaryam", "terezipyrope", "vriskaserket",
    "equiuszahhak", "gamzeemakara", "eridanampora", "feferipeixes",
    "damaramegido", "rufiohnitram", "mitunacaptor", "kankrivantas",
    "meulinleijon", "porrimmaryam", "latulapyrope", "araneaserket",
    "horusszahhak", "kurlozmakara", "cronusampora", "meenahpeixes",
    "john", "rose", "dave", "jade", "jane", "roxy", "dirk", "jake",
    "aradia", "tavros", "sollux", "karkat", "nepeta", "kanaya", "terezi", "vriska",
    "equius", "gamzee", "eridan", "feferi", "damara", "rufioh", "mituna", "kankri",
    "meulin", "porrim", "latula", "aranea", "horuss", "kurloz", "cronus", "meenah",
}

