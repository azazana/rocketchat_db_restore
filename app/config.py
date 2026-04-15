# ---------------------------------------------------------------------------
# Allowed template bases
# ---------------------------------------------------------------------------

ALLOWED_TEMPLATEBASES: set[str] = {
    "erp_test",
	"erp_borzenkova",
    "erp_update",
    "erp_ochkasov",
    "erp_chistyakov",
    "erp_ivanus",
    "erp_korchinskiy",
    "erp_lazarenko",
    "erp_yuzhukova",
    "erp_panteleev",
    "erp_gelunov",
    "erp_ulyanov",
    "erp_shtulman"
}

ALLOWED_TELEGRAM_FULL_ACCESS_USER_IDS: set[int] = {
    125318003, # borzenkova
}

ALLOWED_TELEGRAM_OWN_TEMPLATEBASE_BY_USER_ID: dict[int, str] = {
    881153598: "erp_lazarenko",
    1204949195: "erp_ochkasov",
    125318003: "erp_test",
    339703795: "erp_ulyanov",
    338590359: "erp_gelunov",
    225036101: "erp_ivanus",
    597055470: "erp_chistyakov",
}

# ---------------------------------------------------------------------------
# Jenkins target
# ---------------------------------------------------------------------------

JENKINS_URL: str = "http://172.16.0.139:8080"
JENKINS_JOB: str = "restore erp for dev"
